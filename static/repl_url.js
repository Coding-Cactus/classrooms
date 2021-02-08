function check(inputId, buttonId) {
	document.getElementById(inputId).addEventListener("keyup", () => {
		let text = document.getElementById(inputId).value.toLowerCase();
		if (text.substring(0, 7) === "http://") {
			text = text.replace("http://", "https://")
		}
		if (text.substring(0, 17) === "https://repl.it/@" && text.substring(17, text.length).split("/").length === 2 && text.substring(17, text.length).split("/")[0].length >= 2 && text.substring(17, text.length).split("/")[1].length >= 1) {
			document.getElementById(buttonId).disabled = false;
		} else {
			document.getElementById(buttonId).disabled = true;		
		}
	});
}