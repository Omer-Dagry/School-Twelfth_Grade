function toggle_password_visibility() {
    let password_input = document.getElementById("password_input");
    password_input.type = password_input.type === "password" ? "text" : "password";
    let eye = document.getElementById("eye");
    eye.className = eye.className === "fa fa-eye" ? "fa fa-eye-slash" : "fa fa-eye";
    eye.title = eye.title === "Show Password" ? "Hide Password" : "Show Password";
}

function display_msg(msg_, type="error") {
    let msg = document.getElementById("msg");
    if (msg === null) {
        msg = document.createElement("div");
        msg.id = "msg";
        msg.style.color = type === "error" ? "rgb(145, 52, 60)" : "rgb(65, 180, 102)";
        msg.style.marginBottom = "22px";
        if (reset_password_btn != null) box.insertBefore(msg, reset_password_btn);
        else box.insertBefore(msg, submit_btn);
    }
    msg.innerHTML = msg_;
}

async function reset_password_request() {
    reset_password_btn.onclick = null;
    let email = email_input.value, username = username_input.value;
    let status = await eel.reset_password_stage1(email, username)();
    if (!status) {
        display_msg("Error");
    } else {
        email_box.remove();
        username_box.remove();
        reset_password_btn.remove();
        link_login.remove();
        link_signup.remove();
        let msg = document.getElementById("msg");
        if (msg != null) msg.remove();
        box.appendChild(confirmation_code_box);
        box.appendChild(password_box);
        box.appendChild(submit_btn);
    }
    reset_password_btn.onclick = reset_password_request;
}

async function reset_password_confirmation_and_send_pass() {
    submit_btn.onclick = null;
    let confirmation_code = confirmation_code_input.value, password = password_input.value;
    let status = await eel.reset_password_stage2(confirmation_code, password)();
    confirmation_code_box.remove();
    password_box.remove();
    submit_btn.remove();
    box.appendChild(email_box);
    box.appendChild(username_box);
    box.appendChild(reset_password_btn);
    box.appendChild(link_login);
    box.appendChild(link_signup);
    let msg = document.getElementById("msg");
    if (msg != null) msg.remove();
    if (!status) display_msg("Reset password failed !");
    else display_msg("Password has been reset successfully !", type="regular");
    submit_btn.onclick = reset_password_confirmation_and_send_pass;
}


// document.onkeydown = function (e) {
//     if (e.key === "F1" || e.key === "F3" || e.key === "F5" || 
//         e.key === "F7" || e.key === "F12") {
//         return false;
//     }
// };


var email_box = document.getElementById("email_box");
var username_box = document.getElementById("username_box");
var reset_password_btn = document.getElementById("reset_password_btn");
var link_login = document.getElementById("have_account");
var link_signup = document.getElementById("no_account");

/* Confirmation code stage */

var confirmation_code_box = document.createElement("div");
confirmation_code_box.id = "confirmation_code_box";
var confirmation_code_input = document.createElement("input");
confirmation_code_input.id = "confirmation_code_input";
confirmation_code_input.type = "text";
confirmation_code_input.placeholder = "Confirmation code";
confirmation_code_box.appendChild(confirmation_code_input);

var password_box = document.createElement("div");
password_box.id = "password_box";
var password_icon = document.createElement("i");
password_icon.className = "fa fa-lock";
password_icon.title = "password";
password_box.appendChild(password_icon);
var password_input = document.createElement("input");
password_input.id = "password_input";
password_input.type = "password";
password_input.placeholder = "Password";
password_box.appendChild(password_input);
var password_eye = document.createElement("i");
password_eye.className = "fa fa-eye";
password_eye.id = "eye";
password_eye.title = "Show Password";
password_eye.onclick = toggle_password_visibility;
password_box.appendChild(password_eye);

var submit_btn = document.createElement("button");
submit_btn.id = "submit";
submit_btn.innerHTML = "Submit";
submit_btn.onclick = reset_password_confirmation_and_send_pass;
var box = document.getElementById("box");
