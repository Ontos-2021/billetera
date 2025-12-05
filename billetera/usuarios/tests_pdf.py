from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class PDFReportTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('exportar_reporte_pdf')

    def test_pdf_generation(self):
        """
        Test that the PDF report view returns a 200 status code and the correct content type.
        """
        try:
            import weasyprint
        except (ImportError, OSError):
            print("Skipping PDF test: WeasyPrint dependencies not found.")
            return

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['Content-Disposition'].startswith('inline; filename="reporte_'))
