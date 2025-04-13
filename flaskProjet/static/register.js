document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    form.addEventListener("submit", (e) => {
      let valid = true;
      ["nomError","prenomError","emailError","dateError","passwordError","confirmPasswordError","statutError"].forEach(id => {
        document.getElementById(id).innerText = "";
      });
  
      const nom = document.getElementById("nom").value.trim();
      const prenom = document.getElementById("prenom").value.trim();
      const email = document.getElementById("email").value.trim();
      const dateNaissance = document.getElementById("date_naissance").value;
      const pwd = document.getElementById("mot_de_passe").value;
      const confirm = document.getElementById("confirmPassword").value;
      const statut = document.getElementById("statut").value;
  
      if (!nom) {
        document.getElementById("nomError").innerText = "Le nom est obligatoire.";
        valid = false;
      }
      if (!prenom) {
        document.getElementById("prenomError").innerText = "Le prénom est obligatoire.";
        valid = false;
      }
      if (!/^\S+@\S+\.\S+$/.test(email)) {
        document.getElementById("emailError").innerText = "E-mail invalide.";
        valid = false;
      }
      if (!dateNaissance) {
        document.getElementById("dateError").innerText = "La date est obligatoire.";
        valid = false;
      }
      if (pwd.length < 8) {
        document.getElementById("passwordError").innerText = "Au moins 8 caractères.";
        valid = false;
      }
      if (confirm !== pwd) {
        document.getElementById("confirmPasswordError").innerText = "Ne correspond pas.";
        valid = false;
      }
      if (statut==="") {
        document.getElementById("statutError").innerText = "Sélection requise.";
        valid = false;
      }
      if (!valid) e.preventDefault();
    });
  });

  