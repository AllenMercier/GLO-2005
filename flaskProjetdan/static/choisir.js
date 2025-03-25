
function choisirJeu(){

	var inputElement = document.getElementById("choix");

    var newTodoText = inputElement.value;

    postTodo(newTodoText)
}

function postTodo(text) {
    postUrl = "add-todo"

    fetch(postUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: text
        })
    }).then(function(response) {
        return response.json()
    }).then(function(data) {
        console.log("worked")
    })
}









