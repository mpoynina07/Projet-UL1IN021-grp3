<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MailBox - Connexion</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 20px;
        }

        .login-card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .logo {
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 18px;
            color: #666;
            margin-bottom: 30px;
            font-weight: 500;
        }

        h2 {
            font-size: 24px;
            color: #333;
            margin-bottom: 40px;
            font-weight: 600;
        }

        .input-group {
            text-align: left;
            margin-bottom: 25px;
        }

        label {
            display: block;
            color: #333;
            margin-bottom: 8px;
            font-weight: 500;
        }

        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
        }

        .login-btn {
            width: 100%;
            background: #667eea;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 10px;
        }

        .login-btn:hover {
            background: #5a6fd8;
        }

        .links {
            margin-top: 25px;
            color: #666;
        }

        .links a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }

        .links a:hover {
            text-decoration: underline;
        }

        /* Animation */
        .login-card {
            opacity: 0;
            transform: translateY(30px);
            animation: slideUp 0.6s ease forwards;
        }

        @keyframes slideUp {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <!-- Logo -->
            <div class="logo">MailBox</div>
            
            <!-- Titres -->
            <h1>Se connecter à votre compte</h1>
            
            <!-- Formulaire -->
            <form class="login-form">
                <div class="input-group">
                    <label for="username">Nom d'utilisateur</label>
                    <input type="text" id="username" required>
                </div>
                
                <div class="input-group">
                    <label for="password">Mot de passe</label>
                    <input type="password" id="password" required>
                </div>
                
                <button type="submit" class="login-btn">Se connecter</button>
            </form>
            
            <!-- Lien création compte -->
            <div class="links">
                <p>Pas de compte ? <a href="#">Créer un compte</a></p>
            </div>
        </div>
    </div>

    <script>
        // Gestion de la soumission du formulaire
        document.querySelector('.login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simulation de connexion
            if (username && password) {
                // Ajout d'un effet de chargement sur le bouton
                const btn = document.querySelector('.login-btn');
                btn.textContent = 'Connexion...';
                btn.disabled = true;
                
                // Redirection après un délai
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1000);
            } else {
                alert('Veuillez remplir tous les champs');
            }
        });

        // Animation d'entrée des champs
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input');
            inputs.forEach((input, index) => {
                input.style.opacity = '0';
                input.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    input.style.transition = 'all 0.5s ease';
                    input.style.opacity = '1';
                    input.style.transform = 'translateX(0)';
                }, 300 + (index * 100));
            });
        });
    </script>
</body>
</html>
