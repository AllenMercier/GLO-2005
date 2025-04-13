// Fonction pour vérifier et nettoyer le panier si nécessaire
function verifierCoherencePanier() {
  const panier = JSON.parse(localStorage.getItem('cart') || '[]');
  
  // Si le panier est vide, s'assurer que le formulaire et l'interface sont cohérents
  if (panier.length === 0) {
    document.getElementById('panier-content').style.display = 'none';
    document.getElementById('panier-vide').style.display = 'block';
    document.getElementById('panier-total').textContent = '0.00 $';
    
    // Informer le serveur
    fetch('/vider-panier-api', { method: 'POST' })
      .then(response => console.log('Panier vidé côté serveur'))
      .catch(err => console.error('Erreur synchronisation:', err));
    
    return false;
  }
  
  return true;
}

// Fonction pour mettre à jour les champs cachés du formulaire avec les éléments du panier
function updateCheckoutForm() {
  const panier = JSON.parse(localStorage.getItem('cart') || '[]');
  const container = document.getElementById('hidden-items-container');
  const checkoutButton = document.getElementById('checkout-button');
  
  // Vérifier d'abord la cohérence du panier
  if (!verifierCoherencePanier() && panier.length === 0) {
    checkoutButton.innerHTML = 'Procéder au paiement';
    checkoutButton.disabled = true;
    return;
  }
  
  // Vider le conteneur
  container.innerHTML = '';
  
  // Calculer le total
  let total = 0;
  const duree_location = 2; // Durée fixe de location (2 jours)
  
  // Ajouter les éléments du panier
  panier.forEach(item => {
    // Calculer le prix pour 2 jours (important pour Stripe)
    const prixPourDeuxJours = item.price * duree_location;
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'items[]';
    // Envoi du prix pour 2 jours au lieu du prix journalier
    input.value = `${item.id}:${item.name}:${prixPourDeuxJours}:${item.quantity}`;
    container.appendChild(input);
    
    total += prixPourDeuxJours * item.quantity;
  });
  
  // Mettre à jour le texte du bouton
  checkoutButton.innerHTML = `Procéder au paiement (${total.toFixed(2)} $)`;
  
  // Désactiver le bouton si le panier est vide
  if (panier.length === 0) {
    checkoutButton.disabled = true;
  } else {
    checkoutButton.disabled = false;
  }
  
  console.log("Formulaire mis à jour avec", panier.length, "articles pour un total de", total.toFixed(2), "$");
  console.log("Prix incluant la durée de location de 2 jours");
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
  console.log("DOM chargé, mise à jour du formulaire et vérification de cohérence");
  verifierCoherencePanier();
  updateCheckoutForm();
  
  // Écouter les changements dans le panier
  window.addEventListener('cartUpdated', function() {
    console.log("Événement cartUpdated détecté");
    updateCheckoutForm();
  });
});