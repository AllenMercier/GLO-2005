document.addEventListener('DOMContentLoaded', function() {
    afficherPanier();
});

function afficherPanier() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const container = document.getElementById('panier-items');
    const total = document.getElementById('panier-total');
    const panierVide = document.getElementById('panier-vide');
    
    if (cart.length === 0) {
        panierVide.style.display = 'block';
        return;
    }

    let totalPanier = 0;
    container.innerHTML = '';
    
    cart.forEach(item => {
        const sousTotal = item.price * item.quantity;
        totalPanier += sousTotal;
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.name}</td>
            <td>${item.quantity}</td>
            <td>${item.price}$</td>
            <td>${sousTotal.toFixed(2)}$</td>
            <td>
                <button onclick="supprimerArticle('${item.id}')" class="button danger">
                    Supprimer
                </button>
            </td>
        `;
        container.appendChild(tr);
    });
    
    total.textContent = totalPanier.toFixed(2) + '$';
}

function supprimerArticle(id) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    cart = cart.filter(item => item.id !== id);
    localStorage.setItem('cart', JSON.stringify(cart));
    afficherPanier();
}

function effectuerPaiement() {
    console.log("Fonction effectuerPaiement() appelée");
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    
    if (cart.length === 0) {
        alert('Votre panier est vide.');
        return;
    }
    
    // Afficher un message pour indiquer que la requête est en cours
    console.log("Envoi de la requête à /paiement");
    
    fetch('/paiement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cart)
    })
    .then(response => {
        console.log("Réponse reçue:", response);
        return response.json();
    })
    .then(data => {
        console.log("Données reçues:", data);
        if (data.error) {
            alert('Erreur: ' + data.error);
        } else if (data.checkout_url) {
            console.log("Redirection vers:", data.checkout_url);
            window.location.href = data.checkout_url;
        }
    })
    .catch(error => {
        console.error("Erreur:", error);
        alert('Erreur lors du paiement: ' + error);
    });
}

// Ajouter cette fonction pour vider le panier après un paiement réussi
function clearCart() {
    localStorage.removeItem('cart');
    afficherPanier();
}

// VÉRIFIER : Ces fonctions sont-elles toutes utilisées ?
function updateCartCount() {
    // Cette fonction est-elle appelée partout où elle devrait l'être ?
}