// Ajouter ceci au début du fichier
console.log('cart.js chargé');

// Fonction pour vérifier si une nouvelle session a été créée
(function() {
  // Si un identifiant de session existe déjà dans localStorage, comparer avec l'ID actuel
  const storedSessionId = localStorage.getItem('session_id');
  // Récupérer l'ID de session actuel depuis une balise meta (à ajouter dans base.html)
  const currentSessionId = document.querySelector('meta[name="session-id"]')?.content;
  
  console.log("Vérification de session:", storedSessionId, "vs", currentSessionId);
  
  // Si l'identifiant de session a changé ou n'existait pas, réinitialiser le panier
  if (currentSessionId && (!storedSessionId || storedSessionId !== currentSessionId)) {
    console.log("Nouvelle session détectée, réinitialisation du panier");
    localStorage.setItem('cart', '[]');
    localStorage.setItem('session_id', currentSessionId);
  }
})();

/**
 * Ajoute un article au panier
 */
function addToCart(id, name, price, maxStock) {
  // Vérifier si le stock est à 0
  if (maxStock <= 0) {
    showMessage('Désolé, cet article n\'est plus en stock.', 'error');
    return;
  }

  let cart = JSON.parse(localStorage.getItem('cart') || '[]');
  
  // Calculer la quantité totale actuelle dans le panier
  let totalQuantity = 0;
  for (const item of cart) {
    totalQuantity += item.quantity;
  }
  
  // Recherche si l'article existe déjà
  let item = cart.find(i => i.id === id);
  
  if (item) {
    // Vérifier si l'ajout dépassera la limite de 5
    if (totalQuantity >= 5) {
      showMessage('Vous ne pouvez pas avoir plus de 5 articles dans votre panier.', 'warning');
      return;
    }
    
    // Vérifie le stock avant d'augmenter
    if (item.quantity < maxStock) {
      item.quantity += 1;
    } else {
      showMessage('Stock maximum atteint pour cet article.', 'error');
      return;
    }
  } else {
    // Vérifier si l'ajout d'un nouvel article dépassera la limite de 5
    if (totalQuantity >= 5) {
      showMessage('Vous ne pouvez pas avoir plus de 5 articles dans votre panier.', 'warning');
      return;
    }
    
    // Ajoute nouveau produit
    cart.push({
      id: id,
      name: name,
      price: price,
      quantity: 1,
      maxStock: maxStock
    });
  }
  
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
  
  showMessage(`${name} ajouté au panier`, 'success');
}

/**
 * Affiche un message à l'utilisateur
 */
function showMessage(message, type = 'info') {
  // Supprimer tout message existant
  const existingMessage = document.querySelector('.toast-message');
  if (existingMessage) {
    existingMessage.remove();
  }
  
  // Créer un nouvel élément de message
  const messageElement = document.createElement('div');
  messageElement.className = `toast-message ${type}`;
  messageElement.innerHTML = `
    <p>${message}</p>
    <button class="close-button" onclick="this.parentElement.remove()">×</button>
  `;
  
  document.body.appendChild(messageElement);
  
  // Faire disparaître le message après 3 secondes
  setTimeout(() => {
    messageElement.classList.add('hiding');
    setTimeout(() => {
      if (messageElement.parentElement) {
        messageElement.remove();
      }
    }, 500);
  }, 3000);
}

/**
 * Met à jour l'affichage du compteur du panier
 */
function updateCartCount() {
  let cart = JSON.parse(localStorage.getItem('cart') || '[]');
  let count = 0;
  
  for (let item of cart) {
    count += item.quantity;
  }
  
  const cartCountElement = document.getElementById('cart-count');
  if (cartCountElement) {
    cartCountElement.textContent = count;
    
    // Afficher la notification visuelle si le compteur change
    if (count > 0) {
      cartCountElement.classList.add('has-items');
      setTimeout(() => {
        cartCountElement.classList.remove('has-items');
      }, 500);
    }
  }
}

/**
 * Initialise les fonctionnalités au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
  updateCartCount();
});