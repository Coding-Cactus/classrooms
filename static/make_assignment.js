function mmakeAssignment(type) {
	let request = new XMLHttpRequest();
	request.open("POST", "/get"+type+"assignmentform", true);
	request.onload = function() {
		document.getElementById(type+"-assignment-popup").innerHTML = request.responseText;

		document.getElementById("cancel").addEventListener("click", (e) => {
			document.getElementById(type+"-assignment-popup").innerHTML = "";
			e.preventDefault();
		});
		document.getElementById("close").addEventListener("click", () => {
			document.getElementById(type+"-assignment-popup").innerHTML = "";
		});

		document.getElementById("name").addEventListener("keyup", () => {
			if (document.getElementById("name").value.length > 0 && document.getElementById("instructions").value.length) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById("instructions").addEventListener("keyup", () => {
			if (document.getElementById("instructions").value.length && document.getElementById("name").value.length > 0) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById(type+"-assignment-form").addEventListener("submit", (e) => {
			let request = new XMLHttpRequest();
			request.open('POST', "/"+type+"assignment", true);
			request.onload = function() {
				let response = request.responseText;
				if (response.includes("Invalid")) {
					document.getElementById(type+"-assignment-response").innerHTML = response;
				} else {
					window.location.href = response;
				}
			}
			data = new FormData(e.target)
			data.append("classId", document.getElementById("classroomId").innerHTML);
			request.send(data);
			e.preventDefault();
		});

	};
	data = new FormData();
	data.append("classId", document.getElementById("classroomId").innerHTML);
	request.send(data);
}

if (document.getElementById("make-assignment") !== null) {
	document.getElementById("make-assignment").addEventListener("click", () => mmakeAssignment("make"));
} else {
	document.getElementById("edit-assignment").addEventListener("click", () => mmakeAssignment("edit"));
}