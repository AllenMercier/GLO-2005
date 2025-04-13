document.addEventListener('DOMContentLoaded', function() {
  afficherPanier();
});

function afficherPanier() {
  const panier = JSON.parse(localStorage.getItem('cart') || '[]');
  const panierContent = document.getElementById('panier-content');
  const panierVide = document.getElementById('panier-vide');
  const panierItems = document.getElementById('panier-items');
  
  // Vérifier si le panier est vide
  if (panier.length === 0) {
    // Synchroniser avec le serveur quand le panier est vide côté client
    fetch('/vider-panier-api', { method: 'POST' })
      .then(response => {
        console.log('Panier vide - synchronisation avec serveur effectuée');
      })
      .catch(error => {
        console.error('Erreur lors de la synchronisation du panier vide:', error);
      });
      
    // Mettre à jour l'interface pour le panier vide
    if (panierContent) panierContent.style.display = 'none';
    if (panierVide) panierVide.style.display = 'block';
    
    // Mettre à jour le compteur de panier dans le menu
    updateCartCount();
    return;
  }
  
  // Afficher le contenu du panier
  if (panierContent) panierContent.style.display = 'block';
  if (panierVide) panierVide.style.display = 'none';
  
  // Vider le tableau si l'élément existe
  if (panierItems) panierItems.innerHTML = '';
  
  // Calculer la quantité totale
  let quantiteTotal = 0;
  panier.forEach(item => {
    quantiteTotal += item.quantity;
  });
  
  // Mettre à jour le message d'info s'il existe
  const limiteElement = document.getElementById('limite-panier');
  if (limiteElement) {
    limiteElement.innerHTML = 
      `<p><i class="fas fa-info-circle"></i> Note: ${quantiteTotal} article(s) sur un maximum de 5 dans votre panier.</p>`;
  }
  
  // Afficher chaque article si l'élément de tableau existe
  if (!panierItems) return;
  
  let totalPanier = 0;
  
  panier.forEach(item => {
    const row = document.createElement('tr');
    
    const totalItem = (item.price * item.quantity).toFixed(2);
    totalPanier += parseFloat(totalItem);
    
    row.innerHTML = `
      <td>${item.name}</td>
      <td>${item.price.toFixed(2)} $</td>
      <td>
        <div class="quantity-control">
          <button onclick="modifierQuantite('${item.id}', -1)" class="quantity-btn">-</button>
          <span>${item.quantity}</span>
          <button onclick="modifierQuantite('${item.id}', 1)" class="quantity-btn" ${quantiteTotal >= 5 ? 'disabled' : ''}>+</button>
        </div>
      </td>
      <td>${totalItem} $</td>
      <td>
        <button onclick="supprimerItem('${item.id}')" class="button secondary button-small">Supprimer</button>
      </td>
    `;
    
    panierItems.appendChild(row);
  });
  
  // Mettre à jour le total
  const totalElement = document.getElementById('panier-total');
  if (totalElement) {
    totalElement.textContent = totalPanier.toFixed(2) + ' $';
  }
}

function modifierQuantite(id, changement) {
  let panier = JSON.parse(localStorage.getItem('cart') || '[]');
  
  // Calculer la quantité totale actuelle
  let quantiteTotal = 0;
  panier.forEach(item => {
    quantiteTotal += item.quantity;
  });
  
  // Trouver l'article
  const itemIndex = panier.findIndex(item => item.id === id);
  
  if (itemIndex !== -1) {
    const item = panier[itemIndex];
    
    // Vérifier si on peut augmenter
    if (changement > 0) {
      if (quantiteTotal >= 5) {
        showMessage('Vous ne pouvez pas avoir plus de 5 articles dans votre panier.', 'warning');
        return;
      }
      
      if (item.quantity >= item.maxStock) {
        showMessage('Stock maximum atteint pour cet article.', 'error');
        return;
      }
    }
    
    // Modifier la quantité
    item.quantity += changement;
    
    // Supprimer l'article si la quantité est 0
    if (item.quantity <= 0) {
      panier.splice(itemIndex, 1);
    }
    
    // Sauvegarder et mettre à jour l'affichage
    localStorage.setItem('cart', JSON.stringify(panier));
    updateCartCount();
    afficherPanier();
    // Déclencher un événement personnalisé pour informer que le panier a été mis à jour
    window.dispatchEvent(new Event('cartUpdated'));
  }
}

function supprimerItem(id) {
  let panier = JSON.parse(localStorage.getItem('cart') || '[]');
  panier = panier.filter(item => item.id !== id);
  localStorage.setItem('cart', JSON.stringify(panier));
  updateCartCount();
  afficherPanier();
  // Déclencher un événement personnalisé pour informer que le panier a été mis à jour
  window.dispatchEvent(new Event('cartUpdated'));
}

function viderPanier() {
  if (confirm('Êtes-vous sûr de vouloir vider votre panier ?')) {
    // Vider le panier côté client
    localStorage.setItem('cart', '[]');
    updateCartCount();
    afficherPanier();
    
    // Synchroniser avec le serveur - Envoyer une requête pour vider la session
    fetch('/vider-panier-api', { method: 'POST' })
      .then(response => {
        if (response.ok) {
          console.log('Session panier vidée avec succès côté serveur');
        } else {
          console.error('Erreur lors du vidage de la session panier');
        }
      })
      .catch(error => {
        console.error('Erreur réseau:', error);
      });
    
    // Déclencher un événement personnalisé pour informer que le panier a été mis à jour
    window.dispatchEvent(new Event('cartUpdated'));
  }
}

function effectuerPaiement() {
  // Obtenir l'URL depuis l'élément de données
  const paiementUrlElement = document.getElementById('paiement-url');
  
  if (paiementUrlElement && paiementUrlElement.dataset.url) {
    window.location.href = paiementUrlElement.dataset.url;
  } else {
    // Fallback au cas où l'élément n'est pas trouvé
    console.error("L'URL de paiement n'a pas été trouvée dans le DOM");
    
    // Essayez d'utiliser directement l'URL
    window.location.href = "/paiement";
  }
}

// Fonction pour afficher un message
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

function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('cart') || '[]');
  let count = 0;
  
  for (const item of cart) {
    count += item.quantity;
  }
  
  const cartCountElement = document.getElementById('cart-count');
  if (cartCountElement) {
    cartCountElement.textContent = count;
  }
}