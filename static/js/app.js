// AuraCash - Versão Simplificada
console.log("AuraCash JS carregado!");

// Formulário de Login
const loginForm = document.querySelector('form[action*="login"]');
if (loginForm) {
    console.log("Formulário de login encontrado");
    loginForm.addEventListener('submit', function(e) {
        console.log("Tentando fazer login...");
        // Deixa o formulário ser enviado normalmente
    });
}

// Formulário de Cadastro  
const registerForm = document.querySelector('.cadastrar-form');
if (registerForm) {
    console.log("Formulário de cadastro encontrado");
    registerForm.addEventListener('submit', function(e) {
        console.log("Tentando cadastrar...");
        // Deixa o formulário ser enviado normalmente
    });
}

// Logout
const logoutLinks = document.querySelectorAll('#logoutLink');
logoutLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        console.log("Fazendo logout...");
        window.location.href = '/logout';
    });
});

// Notificações simples
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        border-radius: 8px;
        color: white;
        background: ${type === 'error' ? '#dc3545' : '#17a2b8'};
        z-index: 10000;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// No final do arquivo, adicione esta função:
function setupLogout() {
    const logoutLinks = document.querySelectorAll('#logoutLink');
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Fazendo logout...");
            
            // Fazer logout via JavaScript
            fetch('/logout')
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    }
                })
                .catch(error => {
                    console.error('Erro no logout:', error);
                    window.location.href = '/login';
                });
        });
    });
}

// E chame a função no init ou no DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    setupLogout();
    // ... outro código de inicialização
});