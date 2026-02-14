import os
import re
import subprocess
import tempfile
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class LaTeXPaperGenerator:
    """
    Generates publication-quality PDF research papers from markdown reports using LaTeX.
    Converts structured markdown → LaTeX → PDF with proper citations.
    """

    MACOS_LATEX_PATHS = [
        "/Library/TeX/texbin",
        "/usr/local/texlive/2025/bin/universal-darwin",
        "/usr/local/texlive/2024/bin/universal-darwin",
        "/usr/local/texlive/2023/bin/universal-darwin",
        "/opt/homebrew/bin",
    ]

    def __init__(self, research_data: Dict[str, Any]):
        """
        Initialize the PDF generator.

        Args:
            research_data: Dictionary containing:
                - query: str - Research question
                - answer: str - Markdown report
                - sources: List[Dict] - Source citations
                - quality_assessment: Optional[Dict] - Quality score
        """
        self.query = research_data.get("query", "Research Report")
        self.markdown_report = research_data.get("answer", "")
        self.sources = research_data.get("sources", [])
        self.quality_assessment = research_data.get("quality_assessment", {})

        self.backend_dir = Path(__file__).parent.parent
        self.template_dir = self.backend_dir / "templates"
        self.temp_dir = self.backend_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)

        self.paper_id = hashlib.md5(f"{self.query}{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        self.latex_bin_path = self._find_latex_path()
        self.pdflatex_cmd = str(self.latex_bin_path / "pdflatex") if self.latex_bin_path else "pdflatex"
        self.bibtex_cmd = str(self.latex_bin_path / "bibtex") if self.latex_bin_path else "bibtex"

        self._stopwords = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "have",
            "how",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "or",
            "that",
            "the",
            "to",
            "was",
            "were",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "with",
            "about",
            "into",
            "between",
            "within",
            "without",
            "via",
            "using",
            "use",
            "used",
            "based",
            "across",
        }

    def generate_pdf(self, citation_style: str = "IEEE") -> str:
        """
        Main method to generate PDF from markdown report.

        Args:
            citation_style: BibTeX style (IEEE, APA, ACM, etc.)

        Returns:
            Path to generated PDF file
        """
        print(f"Generating LaTeX PDF for paper {self.paper_id}...")

        try:
            self._check_latex_installation()

            sections = self._parse_markdown_structure()

            latex_content = self._markdown_to_latex(sections)

            bib_path = self._generate_bibtex()

            tex_path = self._build_tex_file(latex_content, citation_style)

            pdf_path = self._compile_latex(tex_path)

            print(f"PDF generated successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

    def _find_latex_path(self) -> Optional[Path]:
        """
        Find LaTeX binary path on the system.
        Checks common installation locations on macOS.

        Returns:
            Path to LaTeX binaries directory, or None if using system PATH
        """
        try:
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                latex_path = Path(result.stdout.strip()).parent
                print(f"Found LaTeX in PATH: {latex_path}")
                return latex_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        for path_str in self.MACOS_LATEX_PATHS:
            path = Path(path_str)
            if (path / "pdflatex").exists() and (path / "bibtex").exists():
                print(f"Found LaTeX at: {path}")
                return path

        print("LaTeX not found in common paths, will try system PATH")
        return None

    def _check_latex_installation(self):
        """Check if pdflatex and bibtex are installed."""
        try:
            subprocess.run([self.pdflatex_cmd, "--version"], capture_output=True, check=True, timeout=5)
            subprocess.run([self.bibtex_cmd, "--version"], capture_output=True, check=True, timeout=5)
            print(f"LaTeX installation verified: {self.pdflatex_cmd}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"LaTeX not found! Tried: {self.pdflatex_cmd}\n"
                "Please install:\n"
                "  macOS: brew install --cask basictex\n"
                "  Linux: sudo apt-get install texlive-latex-base texlive-latex-extra\n"
                f"Error: {e}"
            )

    def _parse_markdown_structure(self) -> Dict[str, str]:
        """
        Parse markdown report into logical sections for academic paper.

        Returns:
            Dictionary with sections: abstract, introduction, findings, etc.
        """
        print("Parsing markdown structure...")

        sections = {"abstract": "", "introduction": "", "methodology": "", "findings": "", "discussion": "", "conclusion": ""}

        lines = self.markdown_report.split("\n")
        current_section = None
        current_content = []
        section_order: List[str] = []

        for line in lines:
            header_match = re.match(r"^#{1,3}\s+(.+)$", line)
            if header_match:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    section_order.append(current_section)

                section_title = header_match.group(1).lower()
                current_content = []

                if "abstract" in section_title or "executive summary" in section_title:
                    current_section = "abstract"
                elif (
                    "introduction" in section_title
                    or "background" in section_title
                    or "related work" in section_title
                    or "literature" in section_title
                ):
                    current_section = "introduction"
                elif "method" in section_title or "approach" in section_title:
                    current_section = "methodology"
                elif "finding" in section_title or "result" in section_title or "analysis" in section_title:
                    current_section = "findings"
                elif "discussion" in section_title or "implication" in section_title or "limitation" in section_title:
                    current_section = "discussion"
                elif (
                    "conclusion" in section_title
                    or ("summary" in section_title and sections.get("abstract"))
                    or "future work" in section_title
                ):
                    current_section = "conclusion"
                else:
                    current_section = "findings"
            else:
                if current_section:
                    current_content.append(line)

        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()
            section_order.append(current_section)

        if not any(sections.values()):
            paragraphs = [p.strip() for p in self.markdown_report.split("\n\n") if p.strip()]
            if paragraphs:
                sections["abstract"] = paragraphs[0][:500]  # First 500 chars
                sections["findings"] = "\n\n".join(paragraphs)

        if sections["findings"] and not sections["discussion"]:
            findings_paras = [p for p in sections["findings"].split("\n\n") if p.strip()]
            if len(findings_paras) > 1:
                sections["discussion"] = findings_paras[-1]

        if sections["findings"] and not sections["conclusion"]:
            findings_paras = [p for p in sections["findings"].split("\n\n") if p.strip()]
            if findings_paras:
                tail = findings_paras[-1]
                sections["conclusion"] = tail[:600] if len(tail) > 600 else tail

        if not sections["abstract"] and sections["findings"]:
            first_para = sections["findings"].split("\n\n")[0]
            sections["abstract"] = first_para[:500] if len(first_para) > 500 else first_para

        print(f"Parsed sections: {[k for k, v in sections.items() if v]}")
        return sections

    def _markdown_to_latex(self, sections: Dict[str, str]) -> str:
        """
        Convert markdown sections to LaTeX format.

        Args:
            sections: Dictionary of section name -> markdown content

        Returns:
            LaTeX formatted content
        """
        print("Converting markdown to LaTeX...")

        latex_sections = []

        section_map = {
            "introduction": "Introduction",
            "methodology": "Methodology",
            "findings": "Findings",
            "discussion": "Discussion",
            "conclusion": "Conclusion",
        }

        for section_key, section_title in section_map.items():
            content = sections.get(section_key, "")
            if content:
                latex_content = self._convert_markdown_to_latex(content)
                latex_sections.append(f"\\section{{{section_title}}}\n{latex_content}\n")

        return "\n".join(latex_sections)

    def _convert_markdown_to_latex(self, markdown_text: str) -> str:
        """
        Convert markdown syntax to LaTeX commands.

        Args:
            markdown_text: Markdown formatted text

        Returns:
            LaTeX formatted text
        """
        text = markdown_text

        text = self._escape_latex_chars(text)

        text = re.sub(r"^###\s+(.+)$", r"\\subsection{\1}", text, flags=re.MULTILINE)
        text = re.sub(r"^####\s+(.+)$", r"\\subsubsection{\1}", text, flags=re.MULTILINE)

        text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)

        text = re.sub(r"\*(.+?)\*", r"\\textit{\1}", text)

        text = re.sub(r"`([^`]+)`", r"\\texttt{\1}", text)

        max_source = max(len(self.sources), 1)

        def replace_citation(match):
            idx = int(match.group(1))
            safe_idx = min(idx, max_source)
            return f"\\cite{{source{safe_idx}}}"

        text = re.sub(r"\[(\d+)\]", replace_citation, text)

        text = self._convert_lists(text)

        text = self._convert_code_blocks(text)

        text = self._convert_tables(text)

        text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\\href{\2}{\1}", text)

        return text

    def _escape_latex_chars(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    def _convert_lists(self, text: str) -> str:
        """Convert markdown lists to LaTeX itemize/enumerate."""
        lines = text.split("\n")
        result = []
        in_list = False
        in_enum = False

        for line in lines:
            if re.match(r"^\s*[-*]\s+", line):
                if not in_list:
                    if in_enum:
                        result.append("\\end{enumerate}")
                        in_enum = False
                    result.append("\\begin{itemize}")
                    in_list = True
                item_text = re.sub(r"^\s*[-*]\s+", "", line)
                result.append(f"  \\item {item_text}")
            elif re.match(r"^\s*\d+\.\s+", line):
                if not in_enum:
                    if in_list:
                        result.append("\\end{itemize}")
                        in_list = False
                    result.append("\\begin{enumerate}")
                    in_enum = True
                item_text = re.sub(r"^\s*\d+\.\s+", "", line)
                result.append(f"  \\item {item_text}")
            else:
                if in_list:
                    result.append("\\end{itemize}")
                    in_list = False
                if in_enum:
                    result.append("\\end{enumerate}")
                    in_enum = False
                result.append(line)

        if in_list:
            result.append("\\end{itemize}")
        if in_enum:
            result.append("\\end{enumerate}")

        return "\n".join(result)

    def _convert_code_blocks(self, text: str) -> str:
        """Convert markdown code blocks to LaTeX verbatim (compatible with BasicTeX)."""

        def replace_code_block(match):
            language = match.group(1) or ""
            code = match.group(2)
            return f"\\begin{{verbatim}}\n{code}\n\\end{{verbatim}}"

        text = re.sub(r"```(\w+)?\n(.*?)```", replace_code_block, text, flags=re.DOTALL)
        return text

    def _convert_tables(self, text: str) -> str:
        """Convert markdown tables to LaTeX tabular with booktabs."""
        lines = text.split("\n")
        output = []
        table_lines: List[str] = []
        in_table = False

        def flush_table():
            if not table_lines:
                return []
            rows = []
            for row in table_lines:
                cells = [c.strip() for c in row.strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                rows.append(cells)
            if not rows:
                return []
            col_count = max(len(r) for r in rows)
            col_spec = "l" * col_count
            latex = ["\\begin{longtable}{%s}" % col_spec, "\\toprule"]
            header = rows[0]
            latex.append(" & ".join(header) + " \\\\")
            latex.append("\\midrule")
            for row in rows[1:]:
                padded = row + [""] * (col_count - len(row))
                latex.append(" & ".join(padded) + " \\\\")
            latex.append("\\bottomrule")
            latex.append("\\end{longtable}")
            return latex

        for line in lines:
            if "|" in line and re.match(r"^\s*\|?.*\|.*$", line):
                table_lines.append(line)
                in_table = True
            else:
                if in_table:
                    output.extend(flush_table())
                    table_lines = []
                    in_table = False
                output.append(line)

        if in_table:
            output.extend(flush_table())

        return "\n".join(output)

    def _generate_bibtex(self) -> str:
        """
        Generate BibTeX file from sources.

        Returns:
            Path to .bib file
        """
        print(f"Generating BibTeX with {len(self.sources)} sources...")

        bib_entries = []

        for idx, source in enumerate(self.sources, 1):
            source_id = f"source{idx}"
            source_type = source.get("source_type", "misc")
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            authors = source.get("authors", [])

            clean_title = self._escape_bibtex_text(title)
            clean_url = self._escape_bibtex_text(url)

            if source_type == "arxiv":
                author_str = " and ".join(authors) if authors else "Unknown"
                author_str = self._escape_bibtex_text(author_str)
                arxiv_id = url.split("/")[-1] if "arxiv.org" in url else ""

                bib_entry = f"""@article{{{source_id},
                            author = {{{author_str}}},
                            title = {{{clean_title}}},
                            journal = {{arXiv preprint}},
                            year = {{{datetime.now().year}}},
                            eprint = {{{arxiv_id}}},
                            url = {{{clean_url}}}
                            }}"""
            else:
                access_note = self._escape_bibtex_text(f"Accessed: {datetime.now().strftime('%Y-%m-%d')}")
                bib_entry = f"""@misc{{{source_id},
                            title = {{{clean_title}}},
                            year = {{{datetime.now().year}}},
                            url = {{{clean_url}}},
                            note = {{{access_note}}}
                            }}"""

            bib_entries.append(bib_entry)

        bib_path = self.temp_dir / f"{self.paper_id}.bib"
        bib_content = "\n\n".join(bib_entries)

        with open(bib_path, "w", encoding="utf-8") as f:
            f.write(bib_content)

        print(f"BibTeX file created: {bib_path}")
        return str(bib_path)

    def _escape_bibtex_text(self, text: str) -> str:
        """Escape LaTeX special characters in BibTeX fields."""
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        escaped = text
        for char, replacement in replacements.items():
            escaped = escaped.replace(char, replacement)
        return escaped

    def _build_tex_file(self, latex_content: str, citation_style: str) -> str:
        """
        Build complete .tex file from template.

        Args:
            latex_content: LaTeX formatted content sections
            citation_style: BibTeX citation style

        Returns:
            Path to .tex file
        """
        print("Building .tex file from template...")

        template_path = self.template_dir / "research_paper.tex"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        sections = self._parse_markdown_structure()
        abstract = sections.get("abstract", "This report presents an AI-generated research analysis.")

        keywords = ", ".join(self._extract_keywords(self.query))

        title = self._escape_latex_chars(self.query)
        short_title = title[:50] + "..." if len(title) > 50 else title

        style_map = {"IEEE": "unsrt", "APA": "apalike", "ACM": "unsrt", "Nature": "plain"}
        bib_style = style_map.get(citation_style, "unsrt")

        latex_content = self._sanitize_citations(latex_content)
        abstract = self._sanitize_citations(self._convert_markdown_to_latex(abstract))

        tex_content = template.replace("{{TITLE}}", title)
        tex_content = tex_content.replace("{{SHORT_TITLE}}", short_title)
        tex_content = tex_content.replace("{{DATE}}", datetime.now().strftime("%B %d, %Y"))
        tex_content = tex_content.replace("{{ABSTRACT}}", abstract)
        tex_content = tex_content.replace("{{KEYWORDS}}", keywords)
        tex_content = tex_content.replace("{{CONTENT}}", latex_content)
        tex_content = tex_content.replace("BIBFILE", self.paper_id)
        tex_content = tex_content.replace("IEEEtran", bib_style)

        tex_path = self.temp_dir / f"{self.paper_id}.tex"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        print(f".tex file created: {tex_path}")
        return str(tex_path)

    def _sanitize_citations(self, text: str) -> str:
        """Clamp citation indices to available sources to avoid undefined refs."""
        max_source = max(len(self.sources), 1)

        def replace_cite(match: re.Match) -> str:
            idx = int(match.group(1))
            safe_idx = min(idx, max_source)
            return f"\\cite{{source{safe_idx}}}"

        return re.sub(r"\\cite\{source(\d+)\}", replace_cite, text)

    def _extract_keywords(self, text: str, max_keywords: int = 6) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z\-]{1,}", text.lower())
        filtered = [w for w in words if w not in self._stopwords and len(w) > 2]
        seen = []
        for w in filtered:
            if w not in seen:
                seen.append(w)
        return [w.capitalize() for w in seen[:max_keywords]]

    def _compile_latex(self, tex_path: str) -> str:
        """
        Compile LaTeX to PDF using pdflatex and bibtex.

        Args:
            tex_path: Path to .tex file

        Returns:
            Path to generated PDF
        """
        print("Compiling LaTeX to PDF...")

        tex_file = Path(tex_path)
        work_dir = tex_file.parent
        base_name = tex_file.stem

        try:
            print("  1/4 Running pdflatex (1st pass)...")
            subprocess.run(
                [self.pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(work_dir), str(tex_file)],
                capture_output=True,
                check=True,
                timeout=30,
                cwd=work_dir,
            )

            print("  2/4 Running bibtex...")
            subprocess.run(
                [self.bibtex_cmd, base_name],
                capture_output=True,
                check=False,  # bibtex may warn but still succeed
                timeout=30,
                cwd=work_dir,
            )

            print("  3/4 Running pdflatex (2nd pass)...")
            subprocess.run(
                [self.pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(work_dir), str(tex_file)],
                capture_output=True,
                check=True,
                timeout=30,
                cwd=work_dir,
            )

            print("  4/4 Running pdflatex (3rd pass)...")
            result = subprocess.run(
                [self.pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(work_dir), str(tex_file)],
                capture_output=True,
                check=True,
                timeout=30,
                cwd=work_dir,
            )

            pdf_path = work_dir / f"{base_name}.pdf"

            if not pdf_path.exists():
                raise RuntimeError("PDF compilation succeeded but PDF file not found")

            print(f"PDF compiled successfully: {pdf_path}")
            return str(pdf_path)

        except subprocess.TimeoutExpired:
            raise RuntimeError("LaTeX compilation timed out (>30s)")
        except subprocess.CalledProcessError as e:
            log_path = work_dir / f"{base_name}.log"
            error_msg = f"LaTeX compilation failed. Check log: {log_path}"
            if log_path.exists():
                with open(log_path, "r") as f:
                    log_tail = f.readlines()[-50:]  # Last 50 lines
                    error_msg += f"\n\nLast log lines:\n{''.join(log_tail)}"
            raise RuntimeError(error_msg)

    def cleanup(self, keep_pdf: bool = True):
        """
        Clean up temporary LaTeX files.

        Args:
            keep_pdf: If True, only delete .tex, .bib, .aux, .log files
        """
        print("🧹 Cleaning up temporary files...")

        patterns = [".tex", ".bib", ".aux", ".log", ".blg", ".bbl", ".out"]
        if not keep_pdf:
            patterns.append(".pdf")

        for pattern in patterns:
            file_path = self.temp_dir / f"{self.paper_id}{pattern}"
            if file_path.exists():
                file_path.unlink()
                print(f"  Deleted: {file_path.name}")


def generate_research_pdf(research_data: Dict[str, Any], citation_style: str = "IEEE") -> str:
    """
    Convenience function to generate PDF from research data.

    Args:
        research_data: Research result dictionary
        citation_style: BibTeX citation style (IEEE, APA, ACM, Nature)

    Returns:
        Path to generated PDF file
    """
    generator = LaTeXPaperGenerator(research_data)
    pdf_path = generator.generate_pdf(citation_style)
    return pdf_path
