document.addEventListener("DOMContentLoaded", function() {
	const searchForm = document.getElementById("searchForm");
	
	searchForm.addEventListener("submit", function(e) {
	  // Réinitialisation des messages d'erreur
	  document.getElementById("nameError").innerText = "";
	  document.getElementById("categoryError").innerText = "";
	  
	  let valid = true;
	  const gameName = document.getElementById("gameName").value.trim();
	  const category = document.getElementById("category").value;
	  
	  // Validation du nom du jeu
	  if (gameName === "") {
		document.getElementById("nameError").innerText = "Veuillez entrer le nom du jeu.";
		valid = false;
	  }
	  
	  // Validation de la catégorie
	  if (category === "") {
		document.getElementById("categoryError").innerText = "Veuillez sélectionner une catégorie.";
		valid = false;
	  }
	  
	  // Empêcher la soumission en cas d'erreur
	  if (!valid) {
		e.preventDefault();
		return;
	  }
	  
	  // Affichage simulé des résultats de recherche
	  const resultsDiv = document.getElementById("searchResults");
	  resultsDiv.innerHTML = `
		<h3>Résultats de recherche</h3>
		<p>Résultats pour <strong>${gameName}</strong> dans la catégorie <strong>${category}</strong> :</p>
		<ul>
		  <li>${gameName} Deluxe Edition</li>
		  <li>${gameName} Retro Version</li>
		  <li>${gameName} Collector's Item</li>
		</ul>
	  `;
	});
  });
  