document.getElementById("set-repl").addEventListener("submit", (e) => {
	let request = new XMLHttpRequest();
	request.open("POST", "/setrepl", true);
	request.onload = function() {
		if (request.responseText === "Success") {
			location.reload();
		} else {
			document.getElementById("setrepl-response").innerHTML = request.responseText;
		}
	}
	request.send(new FormData(e.target));
	e.preventDefault();
});