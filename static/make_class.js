function makeClass(type) {
	let request = new XMLHttpRequest();
	if (type === "make") {
		request.open("GET", "/get"+type+"classform", true);
	} else {
		request.open("POST", "/get"+type+"classform", true);		
	}
	request.onload = function() {
		document.getElementById(type+"-class-popup").innerHTML = request.responseText;
		
		if (type == "edit") {
			document.getElementById("language-select").disabled = true;
		}

		document.getElementById("cancel").addEventListener("click", (e) => {
			document.getElementById(type+"-class-popup").innerHTML = "";
			e.preventDefault();
		});
		document.getElementById("close").addEventListener("click", () => {
			document.getElementById(type+"-class-popup").innerHTML = "";
		});

		document.getElementById("name").addEventListener("keyup", () => {
			if (langs.includes(document.getElementById("language-select").value.toLowerCase()) && document.getElementById("name").value.length > 0) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById("classroom-pfp").addEventListener("change", () => {
			if (langs.includes(document.getElementById("language-select").value.toLowerCase()) && document.getElementById("name").value.length > 0) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById("description").addEventListener("change", () => {
			if (langs.includes(document.getElementById("language-select").value.toLowerCase()) && document.getElementById("name").value.length > 0) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById("language-select").addEventListener("click", () => {	
				document.getElementById("language-select").style.borderColor = "var(--color-primary-1)";		
				document.getElementById("langs").style.display = "block";
				document.getElementById("language-select").style.borderBottomLeftRadius = "0px";
				document.getElementById("language-select").style.borderBottomRightRadius = "0px";
				window.onclick = (e) => {
					if (e.target !== document.getElementById("langs") && e.target !== document.getElementById("language-select") ) {
						if (!(e.target === document.getElementById("close") && e.target === document.getElementById("cancel"))) {
							document.getElementById("langs").style.display = "none";
							document.getElementById("language-select").style.borderBottomLeftRadius = "";
							document.getElementById("language-select").style.borderBottomRightRadius = "";
							document.getElementById("language-select").style.borderColor = "";
							if (langs.includes(document.getElementById("language-select").value.toLowerCase()) && document.getElementById("name").value.length > 0) {
								document.getElementById("submit").disabled = false;
							} else{
								document.getElementById("submit").disabled = true;				
							}
						}
					}
				}
		});

		var langs = [];
		var langDict = {};
		let list = document.getElementById("langs");
		let items = list.querySelectorAll("li");
		items.forEach( item => {
			langs.push(item.dataset.langname.toLowerCase())
			langDict[item.dataset.langname.toLowerCase()] = {
				"name": item.dataset.langname,
				"img": item.firstElementChild.src
			};
			item.addEventListener("click", () => {			
				document.getElementById("language-select").value = item.dataset.langname;
			});
		});

		document.getElementById("language-select").addEventListener("keyup", () => {
			let included = [];
			let resetList = "";
			let typed = document.getElementById("language-select").value.toLowerCase();
			langs.forEach( lang => {
				resetList += "<li data-langname='"+langDict[lang]["name"]+"'><img alt='"+langDict[lang]["name"]+"' src='"+langDict[lang]["img"]+"'><span class='text'>"+langDict[lang]["name"]+"</span></li>"
				if (lang.includes(typed) && typed !== "") {
					included.push(lang);
				}
			});
			document.getElementById("langs").innerHTML = resetList;
			let list = document.getElementById("langs");
			let items = list.querySelectorAll("li");
			items.forEach( item => {
				item.addEventListener("click", () => {			
					document.getElementById("language-select").value = item.dataset.langname;
				});
			});			
			included.sort();
			let i, switching, b, shouldSwitch;
			list = document.getElementById("langs");
			switching = true;
			while (switching) {
				switching = false;
				b = list.getElementsByTagName("LI");
				for (i = 0; i < (b.length-1); i++) {
					shouldSwitch = false;
					current = b[i].dataset.langname.toLowerCase()
					bellow = b[i+1].dataset.langname.toLowerCase()
					if (included.includes(bellow)) {
						if (included.includes(current)) {
							if (included.indexOf(current) > included.indexOf(current)) {
								shouldSwitch = true;
								break;
							}
						} else {
							shouldSwitch = true;
							break;
						}
					}
				}
				if (shouldSwitch) {
					b[i].parentNode.insertBefore(b[i+1], b[i]);
					switching = true;
				}
			}
			switching = true;
			while (switching) {
				switching = false;
				b = list.getElementsByTagName("LI");
				for (i = 0; i < (b.length-1); i++) {
					shouldSwitch = false;
					current = b[i].dataset.langname.toLowerCase()
					bellow = b[i+1].dataset.langname.toLowerCase()
					if (!included.includes(bellow)) {
						break;
					}
					if (b[i].innerHTML.toLowerCase() > b[i+1].innerHTML.toLowerCase()) {
						shouldSwitch = true;
						break;
					}
				}
				if (shouldSwitch) {
					b[i].parentNode.insertBefore(b[i+1], b[i]);
					switching = true;
				}
			}

			if (langs.includes(typed) && document.getElementById("name").value.length > 0) {
				document.getElementById("submit").disabled = false;
			} else{
				document.getElementById("submit").disabled = true;				
			}
		});

		document.getElementById("classroom-pfp").addEventListener("change", (evt) => {
			var tgt = evt.target || window.event.srcElement,
			files = tgt.files;
			
			var fr = new FileReader();
			fr.onload = function () {
				document.getElementById("image-output").src = fr.result;
			}
			fr.readAsDataURL(files[0]);
		});

		document.getElementById(type+"-class-form").addEventListener("submit", (e) => {
			let request = new XMLHttpRequest();
			request.open('POST', "/"+type+"class", true);
			request.onload = function() {
				let response = request.responseText;
				if (response.includes("Invalid")) {
					document.getElementById(type+"-class-response").innerHTML = response;
				} else {
					window.location.href = response;
				}
			}
			data = new FormData(e.target)
			if ( type == "edit") {
				data.append("classId", document.getElementById("classroomId").innerHTML);
			}
			request.send(data);
			e.preventDefault();
		});

	};
	if (type == "make") {
		request.send();
	} else {
		data = new FormData();
		data.append("classId", document.getElementById("classroomId").innerHTML);
		request.send(data);
	}
}

if (document.getElementById("make-class") !== null) {
	document.getElementById("make-class").addEventListener("click", () => makeClass("make"));
} else {
	document.getElementById("edit-class").addEventListener("click", () => makeClass("edit"));
}