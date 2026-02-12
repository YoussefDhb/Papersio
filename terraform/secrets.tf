resource "aws_secretsmanager_secret" "google_api_key" {
  name                    = "${var.project_name}-google-api-key"
  description             = "Google Gemini API key for Papersio"
  recovery_window_in_days = 7
  
  tags = {
    Name = "${var.project_name}-google-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "google_api_key" {
  secret_id     = aws_secretsmanager_secret.google_api_key.id
  secret_string = var.google_api_key
}

resource "aws_secretsmanager_secret" "hf_token" {
  count                   = var.hf_token != "" ? 1 : 0
  name                    = "${var.project_name}-hf-token"
  description             = "Hugging Face token for Papersio"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-hf-token"
  }
}

resource "aws_secretsmanager_secret_version" "hf_token" {
  count         = var.hf_token != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.hf_token[0].id
  secret_string = var.hf_token
}
