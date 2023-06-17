function toggle_password_visibility() {
    let password_input = document.getElementById("password_input");
    password_input.type = password_input.type === "password" ? "text" : "password";
    let eye = document.getElementById("eye");
    eye.className = eye.className === "fa fa-eye" ? "fa fa-eye-slash" : "fa fa-eye";
    eye.title = eye.title === "Show Password" ? "Hide Password" : "Show Password";
}

function display_msg(msg_, type="error") {
    // display message about the status of the signup
    let msg = document.getElementById("msg");
    if (msg === null) {
        msg = document.createElement("div");
        msg.id = "msg";
        msg.style.color = type === "error" ? "rgb(145, 52, 60)" : "rgb(65, 180, 102)";
        msg.style.marginBottom = "22px";
        if (signup_btn != null) box.insertBefore(msg, signup_btn);
        else box.insertBefore(msg, submit_btn);
    }
    msg.innerHTML = msg_;
}

async function signup_request() {
    // signup request (first stage)
    signup_btn.onclick = null;
    email = email_input.value, password = password_input.value, username = username_input.value;
    let [status, reason] = await eel.signup_stage1(email, password, username)();
    if (!status) {
        display_msg(reason);
    } else {
        email_box.remove();
        username_box.remove();
        password_box.remove();
        signup_btn.remove();
        link_login.remove();
        link_reset.remove();
        let msg = document.getElementById("msg");
        if (msg != null) msg.remove();
        box.appendChild(confirmation_code_box);
        box.appendChild(submit_btn);
    }
    signup_btn.onclick = async function () { await signup_request(); };
}

async function signup_confirmation_code() {
    // signup confirmation code stage
    submit_btn.onclick = null;
    let confirmation_code = confirmation_code_input.value;
    let status = await eel.signup_stage2(confirmation_code)();
    confirmation_code_box.remove();
    submit_btn.remove();
    box.appendChild(email_box);
    box.appendChild(username_box);
    box.appendChild(password_box);
    box.appendChild(signup_btn);
    box.appendChild(link_login);
    box.appendChild(link_reset);
    let msg = document.getElementById("msg");
    if (msg != null) msg.remove();
    if (!status) display_msg("Signup failed !");
    else {
        window.email = email;
        window.password = password;
        login();
    }
    submit_btn.onclick = async function() { await signup_confirmation_code(); };
}


document.onkeydown = function (e) {
    if (e.key === "F1" || e.key === "F3" || e.key === "F5" || 
        e.key === "F7" || e.key === "F12") {
        return false; 
    }
};


                                /* Globals */
var email, username, password;
var email_box = document.getElementById("email_box");
var username_box = document.getElementById("username_box");
var password_box = document.getElementById("password_box");
var signup_btn = document.getElementById("signup_btn");
var link_login = document.getElementById("have_account");
var link_reset = document.getElementById("forgot_pass");

/* Confirmation code stage */

var confirmation_code_box = document.createElement("div");
confirmation_code_box.id = "confirmation_code_box";
var confirmation_code_input = document.createElement("input");
confirmation_code_input.id = "confirmation_code_input";
confirmation_code_input.type = "text";
confirmation_code_input.placeholder = "Confirmation code";
confirmation_code_box.appendChild(confirmation_code_input);

var submit_btn = document.createElement("button");
submit_btn.id = "submit";
submit_btn.innerHTML = "Submit";
submit_btn.onclick = signup_confirmation_code;
var box = document.getElementById("box");
