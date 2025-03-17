
function choisirJeu(){

		document.getElementById('contenuOption').innerHTML="Choisir le jeu";
		var selJeu = document.getElementById('selJeu');
		var unJeu;

		selJeu.options[selJeu.options.length] = new Option("Choisir ...");
		for (unJeu of liste){
            unJeu="toto"
			selJeu.options[selJeu.options.length] = new Option(unJeu);

			}


			document.getElementById('selJeu').style.display='block';



	}
