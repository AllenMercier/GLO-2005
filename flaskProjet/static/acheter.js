function addToCart(id, name) {
    let cart = JSON.parse(localStorage.getItem("cart") || "[]");
    cart.push({id, name});
    localStorage.setItem("cart", JSON.stringify(cart));
    alert(name + " a été ajouté au panier.");
  }
  