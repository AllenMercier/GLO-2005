document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    form.addEventListener("submit", (e) => {
      let valid = true;
      document.getElementById("emailError").innerText = "";
      document.getElementById("passwordError").innerText = "";
  
      const email = document.getElementById("email").value.trim();
      const pwd   = document.getElementById("password").value;
  
      if (!email) {
        document.getElementById("emailError").innerText = "L’email est obligatoire.";
        valid = false;
      }
      if (!pwd) {
        document.getElementById("passwordError").innerText = "Le mot de passe est obligatoire.";
        valid = false;
      }
      if (!valid) e.preventDefault();
    });
  });
  