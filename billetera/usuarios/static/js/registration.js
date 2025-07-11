// Función para mostrar/ocultar contraseña
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const button = passwordField.nextElementSibling;
    const icon = button.querySelector('i');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordField.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Validación en tiempo real de las contraseñas
document.addEventListener('DOMContentLoaded', function() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const matchMessage = document.querySelector('.password-match-message');
    const strengthIndicator = document.querySelector('.progress-bar');

    // Función para validar la fortaleza de la contraseña
    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength += 25;
        if (password.match(/[a-z]/)) strength += 25;
        if (password.match(/[A-Z]/)) strength += 25;
        if (password.match(/[0-9]/)) strength += 25;

        strengthIndicator.style.width = strength + '%';
        if (strength < 50) {
            strengthIndicator.className = 'progress-bar bg-danger';
        } else if (strength < 75) {
            strengthIndicator.className = 'progress-bar bg-warning';
        } else {
            strengthIndicator.className = 'progress-bar bg-success';
        }
    }

    // Función para verificar si las contraseñas coinciden
    function checkPasswordsMatch() {
        if (password2.value === '') {
            password2.classList.remove('is-valid', 'is-invalid');
            matchMessage.textContent = '';
            return;
        }

        if (password1.value === password2.value) {
            password2.classList.remove('is-invalid');
            password2.classList.add('is-valid');
            matchMessage.textContent = '¡Las contraseñas coinciden!';
            matchMessage.className = 'password-match-message text-success';
        } else {
            password2.classList.remove('is-valid');
            password2.classList.add('is-invalid');
            matchMessage.textContent = 'Las contraseñas no coinciden';
            matchMessage.className = 'password-match-message text-danger';
        }
    }

    // Event listeners
    password1.addEventListener('input', function() {
        checkPasswordStrength(this.value);
        if (password2.value !== '') {
            checkPasswordsMatch();
        }
    });

    password2.addEventListener('input', checkPasswordsMatch);
});
