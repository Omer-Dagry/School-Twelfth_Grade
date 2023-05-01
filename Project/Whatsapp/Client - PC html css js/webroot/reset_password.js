function toggle_password_visibility() {
    let password_input = document.getElementById("password_input");
    password_input.type = password_input.type === "password" ? "text" : "password";
    let eye = document.getElementById("eye");
    eye.className = eye.className === "fa fa-eye" ? "fa fa-eye-slash" : "fa fa-eye";
}
