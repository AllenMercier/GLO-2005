// Ajouter ceci au début du fichier
console.log('cart.js chargé');

/**
 * Ajoute un article au panier
 */
function addToCart(id, name, price, maxStock) {
  console.log('addToCart appelé avec:', id, name, price, maxStock);
  console.log("Fonction addToCart appelée avec:", id, name, price, maxStock);
  
  // Vérifier si le stock est à 0
  if (maxStock <= 0) {
    alert('Désolé, cet article n\'est plus en stock.');
    return;
  }

  let cart = JSON.parse(localStorage.getItem('cart') || '[]');
  
  // Recherche si l'article existe déjà
  let item = cart.find(i => i.id === id);
  
  if (item) {
    // Vérifie le stock avant d'augmenter
    if (item.quantity < maxStock) {
      item.quantity += 1;
      alert(`Quantité de ${name} mise à jour dans le panier.`);
    } else {
      alert('Stock maximum atteint pour cet article.');
      return;
    }
  } else {
    // Ajoute nouveau produit
    cart.push({
      id: id,
      name: name,
      price: price,
      quantity: 1,
      maxStock: maxStock
    });
    alert(`${name} ajouté au panier.`);
  }
  
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}

/**
 * Met à jour le compteur d'articles dans le panier
 */
function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('cart') || '[]');
  const count = cart.reduce((total, item) => total + item.quantity, 0);
  
  // Si vous avez un élément HTML pour afficher le compteur
  const cartCountElement = document.getElementById('cart-count');
  if (cartCountElement) {
    cartCountElement.textContent = count;
  }
}

/**
 * Initialise les fonctionnalités au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
  updateCartCount();
});