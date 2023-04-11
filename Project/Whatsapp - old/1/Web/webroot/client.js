function assert(condition, message) {
    if (!condition) throw "Assertion failed - " + message;
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function chat_box_left(chat_picture_path, chat_name, last_message, last_message_time) {
    // the div of the entire chat box
    var chat_box_div = document.createElement("div");
    chat_box_div.className = "chat";
    chat_box_div.id = chat_name;
    // chat picture div
    var chat_picture_div = document.createElement("div");
    chat_picture_div.className = "chat-picture";
    chat_picture_div.style.backgroundImage = "url('" + chat_picture_path + "')";
    // chat name div
    var chat_name_div = document.createElement("div");
    chat_name_div.className = "chat-name";
    chat_name_div.innerHTML = chat_name;
    // last message in chat div
    var last_message_div = document.createElement("div");
    last_message_div.className = "chat-last-message";
    last_message_div.innerHTML = last_message;
    // time of last message in chat div
    var last_message_time_div = document.createElement("div");
    last_message_time_div.className = "chat-last-message-time";
    last_message_time_div.innerHTML = last_message_time;

    // get chats list element
    var chats_list = document.getElementById("chats-list-div");
    // append all elements to chat box
    chat_box_div.appendChild(chat_picture_div);
    chat_box_div.appendChild(chat_name_div);
    chat_box_div.appendChild(last_message_div);
    chat_box_div.appendChild(last_message_time_div);
    // chat sep
    var chat_sep = document.createElement("hr");
    chat_sep.classList = "rounded-chat-sep";
    // append chat box to chats list
    chats_list.appendChild(chat_box_div);
    chats_list.appendChild(chat_sep);
    // add event listener
    chat_box_div.addEventListener("click", function() { chat_clicked(chat_name) });
}


function chat_clicked(chat_name) {
    console.log(chat_name);
}

// ----------------------------------------

function reset_chat_and_status_bar() {
    // get chat, status bar - picture, name, last seen
    var chat = document.getElementById("chat");
    var status_bar_picture = document.getElementById("status-bar-picture");
    var status_bar_name = document.getElementById("status-bar-name");
    var status_bar_last_seen = document.getElementById("status-bar-last-seen");
    // reset elements
    chat.innerHTML = "";
    status_bar_picture.innerHTML = "";
    status_bar_picture.style.backgroundImage = "url()";
    status_bar_name.innerHTML = "";
    status_bar_last_seen.innerHTML = "";
}

function handle_msg_length(msg) {
    var max_chars = 55;
    if (msg.length < max_chars) return msg;
    var row_length = 0;
    var i = 0;
    while (i < msg.length) {
        if (msg[i] == " " && row_length > max_chars * 0.6) {
            msg = msg.slice(0, i) + "\n" + msg.slice(i);
            row_length = 0;
        }
        else if (row_length >= max_chars) {
            msg = msg.slice(0, i) + "\n" + msg.slice(i);
            row_length = 0;
            i++;
        }
        row_length += 1;
        i++;
    }
    return msg;
}

/* Create an global msg (from yourself) because it's faster to copy it when creating a new msg */
// msg row
var my_msg_row = document.createElement("div");
my_msg_row.className = "my_msg_row";
// msg box
var my_msg_box = document.createElement("div");
my_msg_box.className = "my_msg_box";
// msg text and time
var my_text_and_time = document.createElement("div");
my_text_and_time.className = "msg_text_and_time";
// msg text
var my_msg_text = document.createElement("div");
my_msg_text.className = "msg_text";
// my_msg_text.innerHTML = msg;
// msg time
var my_msg_time = document.createElement("div");
my_msg_time.className = "msg_time";
// my_msg_time.innerHTML = time;
// append all elements to msg row
my_text_and_time.appendChild(my_msg_text);
my_text_and_time.appendChild(my_msg_time);
my_msg_box.appendChild(my_text_and_time);
my_msg_row.appendChild(my_msg_box);
function msg_from_me(msg, time, position="END") {
    // position: "END" or "START"
    assert(
        position == "END" || position == "START",
        "msg_from_me: param position must be either 'END' or 'START', got '" + position + "'"
    );
    msg = handle_msg_length(msg);
    var this_msg_row = my_msg_row.cloneNode(true);
    this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
    this_msg_row.getElementsByClassName("msg_time")[0].innerHTML = time;
    // append msg row to chat
    var chat = document.getElementById("chat");
    if (position == "END") chat.appendChild(this_msg_row);
    else chat.prepend(this_msg_row);
    // chat.scrollTo(0, chat.scrollHeight);
    // add event listener
    // msg_row.addEventListener("click", function() {func_name(params)})
}

/* Create an global msg (from others) because it's faster to copy it when creating a new msg */
// msg row
var msg_row = document.createElement("div");
msg_row.className = "msg_row";
// msg box
var msg_box = document.createElement("div");
msg_box.className = "msg_box";
// msg text and time
var text_and_time = document.createElement("div");
text_and_time.className = "msg_text_and_time";
// msg text
var msg_text = document.createElement("div");
msg_text.className = "msg_text";
// msg_text.innerHTML = msg;
// msg time
var msg_time = document.createElement("div");
msg_time.className = "msg_time";
// msg_time.innerHTML = time;
// append all elements to msg row
text_and_time.appendChild(msg_text);
text_and_time.appendChild(msg_time);
msg_box.appendChild(text_and_time);
msg_row.appendChild(msg_box);
function msg_from_others(msg, time, position="END") {
    // position: "END" or "START"
    assert(
        position == "END" || position == "START",
        "msg_from_others: param position must be either 'END' or 'START', got '" + position + "'"
    );
    msg = handle_msg_length(msg);
    var this_msg_row = msg_row.cloneNode(true);
    this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
    this_msg_row.getElementsByClassName("msg_time")[0].innerHTML = time;
    // append msg row to chat
    var chat = document.getElementById("chat");
    if (position == "END") chat.appendChild(this_msg_row);
    else chat.prepend(this_msg_row);
    // chat.scrollTo(0, chat.scrollHeight);
    // add event listener
    // msg_row.addEventListener("click", function() {func_name(params)})
}

// ----------------------------------------------------------

function window_active(evt) {
                    /* Change Color Of Search Sep */
    // remove search bar sep
    var search_bar_box = document.getElementById("search_bar_box");
    var sep = document.getElementById("search_bar_sep");
    search_bar_box.removeChild(sep);
    // create new one with green color
    var sep = document.createElement("hr");
    sep.style.borderTop = "1px solid rgb(33, 170, 33)";
    sep.style.borderRadius = "5px";
    sep.style.backgroundColor = "rgb(33, 170, 33)";
    sep.style.borderColor = "rgb(33, 170, 33)";
    sep.id = "search_bar_sep";
    // append it
    search_bar_box.appendChild(sep);
}

function window_inactive(evt) {
                    /* Change Color Of Search Sep */
    // remove search bar sep
    var search_bar_box = document.getElementById("search_bar_box");
    var sep = document.getElementById("search_bar_sep");
    search_bar_box.removeChild(sep);
    // create new one with black color
    var sep = document.createElement("hr");
    sep.style.borderTop = "1px solid black";
    sep.style.borderRadius = "5px";
    sep.style.backgroundColor = "black";
    sep.style.borderColor = "black";
    sep.id = "search_bar_sep";
    // append it
    search_bar_box.appendChild(sep);
}


function addEmoji(emoji) {
    document.getElementById('input_bar').value += emoji;
}
  
function toggleEmojiDrawer() {
    let drawer = document.getElementById('drawer');

    if (drawer.classList.contains('hidden')) {
        drawer.classList.remove('hidden');
    } else {
        drawer.classList.add('hidden');
    }
}


async function demo() {
    console.log("demo");
    // create all chat boxes
    for (var i = 1; i < 200; i ++) chat_box_left('imgs/profile.jpg', "test" + i, "holla", "10:43");
    for (var i = 1; i < 800; i++) {
        msg_from_me("aoiushdfoiahsdfoijasdopifjasopdifjasl;dk1234567890uw3n4yct9o7823y4trc908weymcopgfiuweyr", "18:05", "START");
        msg_from_others("aoiushdfoiahsdfoijasdopifjasopdifjasl;dk12345678909m3cy9t723htf79weuhrfgiuwer", "18:05", "START");
        await sleep(0.01);
    }
    msg_from_me("מה קורה", "18:01", "START");
    // reset_chat_and_status_bar();
    chat.scrollTo(0, chat.scrollHeight);
    console.log("done");
}


function main() {
    // profile picture
    let user_profile_picture = document.getElementById("user-profile-picture");
    user_profile_picture.style.backgroundImage = 'url("imgs/profile.jpg")';
    demo();
    console.log("ok");
    // window active & inactive event listeners
    window.addEventListener('focus', window_active);
    window.addEventListener('blur', window_inactive);
    if (document.hasFocus()) window_active();
    else window_inactive();
    // bind functions
    // let drawer = document.getElementById('drawer');
    // drawer.onclick = toggleEmojiDrawer;
    let send_btn = document.getElementById('send_msg');
    send_btn.addEventListener("click", demo);
}


// eel.expose(main);
main();
