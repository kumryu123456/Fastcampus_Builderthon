"""
Tests for resume upload and analysis functionality.

Constitution Compliance:
- T017-T021: Comprehensive test coverage for User Story 1

Test Coverage:
- T017: Resume model tests
- T018: Resume service tests (upload, extraction, caching)
- T019: Gemini API client tests
- T020: API endpoint tests
- T021: Integration tests
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.models.resume import Resume
from src.models.user import User
from src.services.resume_service import ResumeService
from src.services.gemini_client import GeminiClient


# Fixtures
@pytest.fixture
def test_user(test_db: Session):
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    # Minimal valid PDF structure
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000015 00000 n\n0000000068 00000 n\n0000000125 00000 n\n0000000229 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n322\n%%EOF"


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    Software Engineer

    Experience:
    - Senior Software Engineer at Tech Corp (2020-2024)
      • Led development of microservices architecture
      • Managed team of 5 engineers
      • Improved system performance by 40%

    - Software Engineer at Startup Inc (2018-2020)
      • Built REST APIs with Python and FastAPI
      • Implemented CI/CD pipelines

    Skills: Python, JavaScript, React, Docker, Kubernetes, PostgreSQL, AWS
    Education: BS Computer Science, State University (2018)
    """


@pytest.fixture
def sample_analysis_result():
    """Sample Gemini analysis result."""
    return {
        "strengths": [
            "Strong technical leadership experience",
            "Proven track record of performance improvements",
            "Modern tech stack expertise"
        ],
        "weaknesses": [
            "Limited frontend development details",
            "No certifications mentioned"
        ],
        "recommendations": [
            "Add specific metrics for leadership impact",
            "Include relevant certifications or courses",
            "Expand on frontend projects"
        ],
        "suitable_roles": [
            "Senior Software Engineer",
            "Tech Lead",
            "Engineering Manager"
        ],
        "skills": [
            "Python", "JavaScript", "React", "Docker",
            "Kubernetes", "PostgreSQL", "AWS", "FastAPI", "CI/CD"
        ],
        "experience_years": 6
    }


# T017: Resume Model Tests
class TestResumeModel:
    """Tests for Resume model."""

    def test_compute_file_hash(self):
        """Test file hash computation."""
        content = b"test content"
        hash1 = Resume.compute_file_hash(content)
        hash2 = Resume.compute_file_hash(content)

        assert hash1 == hash2  # Same content = same hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

        # Different content = different hash
        hash3 = Resume.compute_file_hash(b"different content")
        assert hash1 != hash3

    def test_is_analyzed(self, test_db: Session, test_user: User):
        """Test is_analyzed method."""
        resume = Resume(
            user_id=test_user.id,
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="analyzed",
            analysis_result={"strengths": ["test"]},
        )
        test_db.add(resume)
        test_db.commit()

        assert resume.is_analyzed() is True

        # Test without analysis
        resume2 = Resume(
            user_id=test_user.id,
            original_filename="test2.pdf",
            file_path="/uploads/test2.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="uploaded",
        )
        test_db.add(resume2)
        test_db.commit()

        assert resume2.is_analyzed() is False

    def test_get_analysis_summary(self, test_db: Session, test_user: User, sample_analysis_result):
        """Test get_analysis_summary method."""
        resume = Resume(
            user_id=test_user.id,
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="analyzed",
            analysis_result=sample_analysis_result,
        )
        test_db.add(resume)
        test_db.commit()

        summary = resume.get_analysis_summary()

        assert summary["strengths_count"] == 3
        assert summary["weaknesses_count"] == 2
        assert summary["recommendations_count"] == 3
        assert len(summary["suitable_roles"]) == 3


# T018: Resume Service Tests
class TestResumeService:
    """Tests for ResumeService."""

    @pytest.mark.asyncio
    async def test_validate_file_valid_pdf(self, test_db: Session):
        """Test file validation with valid PDF."""
        service = ResumeService(test_db)

        file = UploadFile(
            filename="resume.pdf",
            file=io.BytesIO(b"test content"),
        )
        file.content_type = "application/pdf"

        # Should not raise exception
        service._validate_file(file)

    @pytest.mark.asyncio
    async def test_validate_file_invalid_type(self, test_db: Session):
        """Test file validation with invalid file type."""
        service = ResumeService(test_db)

        file = UploadFile(
            filename="resume.txt",
            file=io.BytesIO(b"test content"),
        )
        file.content_type = "text/plain"

        with pytest.raises(ValueError, match="Invalid file type"):
            service._validate_file(file)

    def test_save_file(self, test_db: Session, tmp_path):
        """Test file saving with UUID filename."""
        service = ResumeService(test_db)
        service.upload_dir = tmp_path  # Use temp directory

        content = b"test content"
        filename = "resume.pdf"

        saved_path = service._save_file(filename, content)

        assert saved_path.exists()
        assert saved_path.parent == tmp_path
        assert saved_path.suffix == ".pdf"
        assert saved_path.name != filename  # UUID filename

        # Verify content
        with open(saved_path, "rb") as f:
            assert f.read() == content

    def test_get_cached_resume(self, test_db: Session, test_user: User, sample_analysis_result):
        """Test caching logic (T026)."""
        service = ResumeService(test_db)

        file_hash = "abc123"

        # No cache initially
        cached = service._get_cached_resume(test_user.id, file_hash)
        assert cached is None

        # Create cached resume
        resume = Resume(
            user_id=test_user.id,
            original_filename="resume.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            file_hash=file_hash,
            status="analyzed",
            analysis_result=sample_analysis_result,
        )
        test_db.add(resume)
        test_db.commit()

        # Should find cached resume
        cached = service._get_cached_resume(test_user.id, file_hash)
        assert cached is not None
        assert cached.id == resume.id
        assert cached.file_hash == file_hash

    @patch("src.services.resume_service.PyPDF2.PdfReader")
    def test_extract_text_from_pdf(self, mock_pdf_reader, test_db: Session, tmp_path):
        """Test PDF text extraction."""
        service = ResumeService(test_db)

        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test resume content"
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance

        # Create temp PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        extracted_text = service._extract_text_from_pdf(pdf_path)

        assert extracted_text == "Test resume content"
        mock_pdf_reader.assert_called_once()


# T019: Gemini API Client Tests
class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_build_resume_analysis_prompt(self):
        """Test prompt building."""
        client = GeminiClient()
        resume_text = "Test resume"

        prompt = client._build_resume_analysis_prompt(resume_text)

        assert "Test resume" in prompt
        assert "strengths" in prompt
        assert "weaknesses" in prompt
        assert "JSON" in prompt

    def test_parse_analysis_response_valid_json(self, sample_analysis_result):
        """Test parsing valid JSON response."""
        client = GeminiClient()

        import json
        response_text = json.dumps(sample_analysis_result)

        parsed = client._parse_analysis_response(response_text)

        assert parsed["strengths"] == sample_analysis_result["strengths"]
        assert parsed["experience_years"] == sample_analysis_result["experience_years"]

    def test_parse_analysis_response_with_markdown(self, sample_analysis_result):
        """Test parsing JSON wrapped in markdown code blocks."""
        client = GeminiClient()

        import json
        response_text = f"```json\n{json.dumps(sample_analysis_result)}\n```"

        parsed = client._parse_analysis_response(response_text)

        assert parsed["strengths"] == sample_analysis_result["strengths"]

    def test_parse_analysis_response_invalid_json(self):
        """Test parsing invalid JSON with fallback."""
        client = GeminiClient()

        response_text = "This is not JSON"

        parsed = client._parse_analysis_response(response_text)

        # Should return fallback structure
        assert "strengths" in parsed
        assert "Unable to parse analysis" in parsed["strengths"]
        assert "parse_error" in parsed


# T020: API Endpoint Tests
@pytest.mark.asyncio
class TestResumeEndpoints:
    """Tests for resume API endpoints."""

    @patch("src.services.gemini_client.genai.GenerativeModel")
    async def test_upload_resume_success(
        self,
        mock_gemini_model,
        client,
        test_db: Session,
        test_user: User,
        sample_pdf_content,
        sample_analysis_result
    ):
        """Test successful resume upload and analysis."""
        # Mock Gemini API response
        mock_response = Mock()
        import json
        mock_response.text = json.dumps(sample_analysis_result)
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_gemini_model.return_value = mock_model_instance

        # Upload file
        files = {"file": ("resume.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

        response = client.post("/api/v1/resume/upload", files=files)

        assert response.status_code == 201
        data = response.json()

        assert "resume_id" in data
        assert data["status"] == "analyzed"
        assert "analysis" in data
        assert len(data["analysis"]["strengths"]) > 0

    async def test_upload_resume_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        files = {"file": ("resume.txt", io.BytesIO(b"text content"), "text/plain")}

        response = client.post("/api/v1/resume/upload", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]["message"]

    async def test_get_resume_analysis_success(
        self,
        client,
        test_db: Session,
        test_user: User,
        sample_analysis_result
    ):
        """Test retrieving resume analysis."""
        # Create resume in database
        resume = Resume(
            user_id=test_user.id,
            original_filename="resume.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="analyzed",
            analysis_result=sample_analysis_result,
        )
        test_db.add(resume)
        test_db.commit()
        test_db.refresh(resume)

        response = client.get(f"/api/v1/resume/{resume.id}/analysis")

        assert response.status_code == 200
        data = response.json()

        assert data["resume_id"] == resume.id
        assert data["status"] == "analyzed"
        assert data["analysis"] is not None

    async def test_get_resume_analysis_not_found(self, client):
        """Test retrieving non-existent resume."""
        response = client.get("/api/v1/resume/99999/analysis")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["message"]


# T021: Integration Tests
@pytest.mark.integration
class TestResumeIntegration:
    """Integration tests for complete resume workflow."""

    @pytest.mark.asyncio
    @patch("src.services.gemini_client.genai.GenerativeModel")
    async def test_complete_workflow_with_caching(
        self,
        mock_gemini_model,
        test_db: Session,
        test_user: User,
        sample_pdf_content,
        sample_analysis_result
    ):
        """Test complete workflow: upload -> analyze -> cache -> re-upload (cached)."""
        # Mock Gemini API
        mock_response = Mock()
        import json
        mock_response.text = json.dumps(sample_analysis_result)
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_gemini_model.return_value = mock_model_instance

        service = ResumeService(test_db)

        # First upload
        file1 = UploadFile(
            filename="resume.pdf",
            file=io.BytesIO(sample_pdf_content),
        )
        file1.content_type = "application/pdf"

        resume1 = await service.upload_and_analyze_resume(file1, test_user.id)

        assert resume1.status == "analyzed"
        assert resume1.analysis_result is not None
        call_count_first = mock_model_instance.generate_content.call_count

        # Second upload with same content (should use cache)
        file2 = UploadFile(
            filename="resume_copy.pdf",
            file=io.BytesIO(sample_pdf_content),
        )
        file2.content_type = "application/pdf"

        resume2 = await service.upload_and_analyze_resume(file2, test_user.id)

        # Should return cached result
        assert resume2.id == resume1.id  # Same resume returned
        # Gemini API should not be called again
        assert mock_model_instance.generate_content.call_count == call_count_first
