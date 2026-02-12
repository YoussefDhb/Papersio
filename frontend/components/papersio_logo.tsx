import Image from 'next/image';

export default function PapersioLogo({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <Image
      src="/papersio-logo.svg"
      alt="Papersio Logo"
      width={28}
      height={28}
      className={className}
    />
  );
}
