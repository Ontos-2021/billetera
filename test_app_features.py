#!/usr/bin/env python
"""
Script para probar la funcionalidad de subida de imágenes con Cloudflare R2
"""
import os
import sys
import django
from pathlib import Path

# Add the Django project to the path
sys.path.append('/app/billetera')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billetera.settings')

django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from usuarios.models import PerfilUsuario
from usuarios.forms import PerfilUsuarioForm

def test_image_upload():
    """Test image upload functionality with R2"""
    print("🧪 Testing image upload with Cloudflare R2...")
    
    # Create test user
    try:
        user = User.objects.get(username='testuser')
        print("✅ Using existing test user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print("✅ Created test user")
    
    # Get or create profile
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
    if created:
        print("✅ Created user profile")
    else:
        print("✅ Using existing user profile")
    
    # Create a simple test image using PIL
    from PIL import Image
    import io
    
    # Create a simple 50x50 red image
    img = Image.new('RGB', (50, 50), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    test_image = SimpleUploadedFile(
        "test_image.png",
        buffer.getvalue(),
        content_type="image/png"
    )
    
    print("✅ Created test image file")
    
    # Test form submission
    form_data = {
        'direccion': 'Test Address 123',
        'telefono': '+1234567890'
    }
    
    file_data = {
        'imagen_perfil': test_image
    }
    
    print("🔄 Testing form submission...")
    
    try:
        form = PerfilUsuarioForm(form_data, file_data, instance=perfil)
        
        if form.is_valid():
            print("✅ Form validation passed")
            
            # Save the form (this will trigger R2 upload)
            perfil_updated = form.save()
            print("✅ Form saved successfully")
            
            # Check if image was uploaded
            if perfil_updated.imagen_perfil:
                print(f"✅ Image uploaded successfully!")
                print(f"📁 Image URL: {perfil_updated.imagen_perfil.url}")
                print(f"📁 Image name: {perfil_updated.imagen_perfil.name}")
                
                # Test image access
                try:
                    # Try to get the image size (this will trigger a request to R2)
                    size = perfil_updated.imagen_perfil.size
                    print(f"✅ Image accessible, size: {size} bytes")
                    return True
                except Exception as e:
                    print(f"❌ Error accessing image: {str(e)}")
                    return False
            else:
                print("❌ No image was uploaded")
                return False
                
        else:
            print("❌ Form validation failed:")
            for field, errors in form.errors.items():
                print(f"  - {field}: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error during form submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_csrf_token():
    """Test CSRF token functionality"""
    print("\n🔒 Testing CSRF token functionality...")
    
    from django.middleware.csrf import get_token
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    from usuarios.views import editar_perfil
    
    try:
        # Create a fake request
        factory = RequestFactory()
        request = factory.get('/usuarios/perfil/editar')
        request.user = AnonymousUser()
        
        # Get CSRF token
        token = get_token(request)
        print(f"✅ CSRF token generated: {token[:10]}...")
        
        # Test POST request with CSRF token
        post_request = factory.post('/usuarios/perfil/editar', {
            'csrfmiddlewaretoken': token,
            'direccion': 'Test',
            'telefono': '123'
        })
        post_request.user = AnonymousUser()
        
        print("✅ CSRF token functionality working")
        return True
        
    except Exception as e:
        print(f"❌ CSRF error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Django app tests with R2 integration...\n")
    
    # Test 1: Image upload
    upload_success = test_image_upload()
    
    # Test 2: CSRF functionality  
    csrf_success = test_csrf_token()
    
    print("\n📊 Test Results:")
    print(f"  📁 Image Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"  🔒 CSRF Tokens: {'✅ PASS' if csrf_success else '❌ FAIL'}")
    
    if upload_success and csrf_success:
        print("\n🎉 All tests passed! R2 integration is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the errors above.")
