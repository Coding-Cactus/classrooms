function remove(type, id) {
	if (confirm("Are you sure you want to remove this " + type + " from this classroom?")) {
		let request = new XMLHttpRequest();
		request.open("POST", "/remove"+type, true);
		request.onload = function() {
			location.reload();
		}
		data = new FormData();
		data.append("class_id", document.getElementById("classroomId").innerHTML);
		data.append(type+"_id", id);
		request.send(data);
	}
}


document.querySelectorAll("td.remove-student").forEach(student => {
	student.addEventListener("click", () => {remove("student", student.dataset.id)});
});
document.querySelectorAll("span.remove-teacher").forEach(teacher => {
	teacher.addEventListener("click", () => {remove("teacher", teacher.dataset.id)});
});