from src.ingestion.sources import generate_file_type_filter


def test_generate_file_type_filter():
    
    supported_files = ["pdf", "docx"]
    result = generate_file_type_filter(supported_files)

    assert result == "mimeType='application/pdf' or mimeType='application/vnd.google-apps.document'"