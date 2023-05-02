function toggle_password_visibility() {
    let password_input = document.getElementById("password_input");
    password_input.type = password_input.type === "password" ? "text" : "password";
    let eye = document.getElementById("eye");
    eye.className = eye.className === "fa fa-eye" ? "fa fa-eye-slash" : "fa fa-eye";
    eye.title = eye.title === "Show Password" ? "Hide Password" : "Show Password";
}

async function login() {
    let login_btn = document.getElementById("login_btn");
    login_btn.onclick = null;
    let email_input = document.getElementById("email_input");
    let password_input = document.getElementById("password_input");
    let email = email_input.value, password = password_input.value;
    let [status, reason] = await eel.login(email, password)();
    if (!status && reason != "Already Logged In") {
        let error_msg = document.getElementById("error_msg");
        if (error_msg === null) {
            error_msg = document.createElement("div");
            error_msg.id = "error_msg";
            error_msg.style.color = "rgb(145, 52, 60)";
            error_msg.style.marginBottom = "22px";
            let box = document.getElementById("box");
            box.insertBefore(error_msg, login_btn);
        }
        error_msg.innerHTML = reason;
    } else {
        window.location = "ChatEase.html";
    }
    login_btn.onclick = login;
}


// document.onkeydown = function (e) {
//     if (e.key === "F1" || e.key === "F3" || e.key === "F5" || 
//         e.key === "F7" || e.key === "F12") {
//         return false;
//     }
// };
