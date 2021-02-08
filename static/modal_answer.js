document.getElementById("set-modal-answer-form").addEventListener("submit", (e) => {
	let request = new XMLHttpRequest();
	request.open("POST", "/setmodalanswer", true);	
	request.onload = function() {
		if (request.responseText == "Success") {
			location.reload();
		} else {
			document.getElementById("set-modal-error").innerHTML = request.responseText;
		}
	}
	request.send(new FormData(e.target));
	e.preventDefault();
});