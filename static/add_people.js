function add_people(type) {
	let request = new XMLHttpRequest();
	request.open("POST", "/getadd"+type+"form", true);
	request.onload = function() {
		document.getElementById("add-"+type+"-popup").innerHTML = request.responseText;
		document.getElementById("close").addEventListener("click", () => {
			document.getElementById("add-"+type+"-popup").innerHTML = "";
		});

		document.getElementById("invite-username").addEventListener("keyup", () => {
			if (document.getElementById("invite-username").value.length >= 2) {
				document.getElementById("invite-submit").disabled = false;
			} else{
				document.getElementById("invite-submit").disabled = true;				
			}
		});

		function copy(elem) {
			input = elem.previousElementSibling
			let text = input.value;
			let copy =  document.createElement('TEXTAREA');
			copy.innerHTML = text;
			document.body.appendChild(copy);
			copy.select();
			document.execCommand("copy");
			input.value = "COPIED!"
			document.body.removeChild(copy);
			setTimeout(() => { input.value = text }, 1000);			
		}

		document.getElementById("invite-link-copy").addEventListener("click", () => copy(document.getElementById("invite-link-copy")));
		document.getElementById("invite-code-copy").addEventListener("click", () => copy(document.getElementById("invite-code-copy")));

	}
	const formData = new FormData();
  	formData.append('classId', document.getElementById("classroomId").innerHTML);
	request.send(formData);
}

document.getElementById("invite-students-button").addEventListener("click", () => add_people("students"));
document.getElementById("invite-teachers-button").addEventListener("click", () => add_people("teachers"));