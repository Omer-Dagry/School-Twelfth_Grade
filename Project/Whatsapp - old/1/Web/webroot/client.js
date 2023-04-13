function assert(condition, message) {
    if (!condition) throw "Assertion failed - " + message;
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function chat_box_left(chat_picture_path, chat_name, last_message, 
    last_message_time, chat_id, chat_type) {
    // the div of the entire chat box
    let chat_box_div = document.createElement("div");
    chat_box_div.className = "chat";
    chat_box_div.id = chat_id;
    chat_box_div.chat_type = chat_type;
    // chat picture div
    let chat_picture_div = document.createElement("div");
    chat_picture_div.className = "chat-picture";
    // if (chat_type === "group") image -> by chat_id else image -> by chat
    chat_picture_div.style.backgroundImage = "url('" + chat_picture_path + "')";
    // chat name div
    let chat_name_div = document.createElement("div");
    chat_name_div.className = "chat-name";
    chat_name_div.innerHTML = chat_name;
    // last message in chat div
    let last_message_div = document.createElement("div");
    last_message_div.className = "chat-last-message";
    last_message_div.innerHTML = last_message;
    // time of last message in chat div
    let last_message_time_div = document.createElement("div");
    last_message_time_div.className = "chat-last-message-time";
    last_message_time_div.innerHTML = last_message_time;
    // get chats list element
    let chats_list = document.getElementById("chats-list-div");
    // append all elements to chat box
    chat_box_div.appendChild(chat_picture_div);
    chat_box_div.appendChild(chat_name_div);
    chat_box_div.appendChild(last_message_div);
    chat_box_div.appendChild(last_message_time_div);
    // chat sep
    let chat_sep = document.createElement("hr");
    chat_sep.classList = "rounded-chat-sep";
    // append chat box to chats list
    chats_list.appendChild(chat_box_div);
    chats_list.appendChild(chat_sep);
    // save refrence to sep
    chat_box_div.sep = chat_sep;
    // add event listener
    chat_box_div.addEventListener("click", function() { load_chat(chat_name, chat_id) });
}


// ----------------------------------------

function reset_chat_and_status_bar() {
    // get chat, status bar - picture, name, last seen
    let chat = document.getElementById("chat");
    let status_bar_picture = document.getElementById("status-bar-picture");
    let status_bar_name = document.getElementById("status-bar-name");
    let status_bar_last_seen = document.getElementById("status-bar-last-seen");
    // reset elements
    chat.innerHTML = "";
    status_bar_picture.innerHTML = "";
    status_bar_picture.style.backgroundImage = "url()";
    status_bar_name.innerHTML = "";
    status_bar_last_seen.innerHTML = "";
}

function handle_msg_length(msg) {
    let max_chars = 55;
    if (msg.length < max_chars) return msg;
    let row_length = 0;
    let i = 0;
    while (i < msg.length) {
        if (msg[i] === " " && row_length > max_chars * 0.6) {
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

/* ----------------------------------------------------------------------- */

function message_options() {

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
// msg sender
var my_msg_sender = document.createElement("div");
my_msg_sender.className = "msg_sender";
// my_msg_sender.innerHTML = sender;
// msg text
var my_msg_text = document.createElement("div");
my_msg_text.className = "msg_text";
// my_msg_text.innerHTML = msg;
// msg time
var my_msg_time = document.createElement("div");
my_msg_time.className = "msg_time";
// my_msg_time.innerHTML = time;
// append all elements to msg row
my_text_and_time.appendChild(my_msg_sender);
my_text_and_time.appendChild(my_msg_text);
my_text_and_time.appendChild(my_msg_time);
my_msg_box.appendChild(my_text_and_time);
my_msg_row.appendChild(my_msg_box);
function msg_from_me(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
    // position: "END" or "START"
    assert(
        position === "END" || position === "START",
        "msg_from_me: param position must be either 'END' or 'START', got '" + position + "'"
    );
    assert(
        msg_type == "msg" || msg_type == "file" || msg_type == "remove" || msg_type == "add",
        "msg_from_me: param msg_type must be either 'msg' or 'file' or 'remove' or 'add', got '" + msg_type + "'"
    );
    if (deleted_for_all) {
        // This message was deleted.
    } else if (username in deleted_for) {
        return;
    } else if (msg_type == "msg") {
        msg = handle_msg_length(msg);
        let this_msg_row = my_msg_row.cloneNode(true);
        this_msg_row.id = 'msg_' + msg_index;
        this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
        this_msg_row.getElementsByClassName("msg_time")[0].innerHTML = time;
        this_msg_row.getElementsByClassName("msg_sender")[0].innerHTML = sender;
        // append msg row to chat
        if (position === "END") chat.appendChild(this_msg_row);
        else chat.prepend(this_msg_row);
        // add event listener
        // msg_row.addEventListener("click", function() {func_name(msg_index, seen_by)}) // left click
    } else if (msg_type == "file") {
        /* TODO
        check if photo, if so, display it, else display a special msg, 
        either way when pressed call a python function that start the file
        */
    } else if (msg_type == "remove" || msg_type == "add") {
        /* TODO
        display the msg in gray (and centered) 
        */
    }

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
// msg sender
var msg_sender = document.createElement("div");
msg_sender.className = "msg_sender";
// msg_sender.innerHTML = sender;
// msg text
var msg_text = document.createElement("div");
msg_text.className = "msg_text";
// msg_text.innerHTML = msg;
// msg time
var msg_time = document.createElement("div");
msg_time.className = "msg_time";
// msg_time.innerHTML = time;
// append all elements to msg row
text_and_time.appendChild(msg_sender);
text_and_time.appendChild(msg_text);
text_and_time.appendChild(msg_time);
msg_box.appendChild(text_and_time);
msg_row.appendChild(msg_box);
function msg_from_others(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
    // position: "END" or "START"
    assert(
        position === "END" || position === "START",
        "msg_from_others: param position must be either 'END' or 'START', got '" + position + "'"
    );
    msg = handle_msg_length(msg);
    let this_msg_row = msg_row.cloneNode(true);
    this_msg_row.id = 'msg_' + msg_index;
    this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
    this_msg_row.getElementsByClassName("msg_time")[0].innerHTML = time;
    this_msg_row.getElementsByClassName("msg_sender")[0].innerHTML = sender;
    // append msg row to chat
    if (position === "END") chat.appendChild(this_msg_row);
    else chat.prepend(this_msg_row);
    // chat.scrollTo(0, chat.scrollHeight);
    // add event listener
    // msg_row.addEventListener("click", function() {func_name(params)})
}

// ----------------------------------------------------------

function window_active(evt) {
                    /* Change Color Of Search Sep */
    // remove search bar sep
    let search_bar_box = document.getElementById("search_bar_box");
    let sep = document.getElementById("search_bar_sep");
    search_bar_box.removeChild(sep);
    // create new one with green color
    sep = document.createElement("hr");
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
    let search_bar_box = document.getElementById("search_bar_box");
    let sep = document.getElementById("search_bar_sep");
    search_bar_box.removeChild(sep);
    // create new one with black color
    sep = document.createElement("hr");
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


async function load_msgs(chat_msgs, position = "END") {
    if (username === null) await ask_for_username;
    let from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time;
    let keys = Object.keys(chat_msgs);
    // sort messages by index
    keys.sort();
    // if adding more messages from the top, start from the most recent one
    if (position === "START") keys.reverse();
    for (let msg_index in chat_msgs) {
        console.log(msg_index);
        [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time] = chat_msgs[msg_index];
        //
        if (username in deleted_for) continue;
        if (from_user === username) {
            msg_from_me(
                from_user, msg, time, msg_index, msg_type, deleted_for, 
                deleted_for_all, seen_by, position
            );
        }
        else {
            msg_from_others(
                from_user, msg, time, msg_index, msg_type, deleted_for, 
                deleted_for_all, seen_by, position
            ); 
        }
        if (last_msg_index < msg_index) last_msg_index = msg_index;
    }
}


async function load_chat(chat_name, chat_id) {
    if (chat_id == chat.chat_id) return;
    last_msg_index = 0;
    console.log(chat_name, chat_id);
    chat.chat_id = chat_id;
    let chat_msgs = JSON.parse(await eel.get_chat_msgs(chat_id)());
    load_msgs(chat_msgs);
    chat.scrollTo(0, chat.scrollHeight);
}


async function load_more_msgs() {
    let first_msg = chat.firstChild;
    let chat_id = chat.chat_id;
    let chat_msgs = JSON.parse(await eel.get_more_msgs()());
    load_msgs(chat_msgs, "START");
    chat.onscroll = check_pos;  // re-allow loading more msgs
    chat.scrollTo(0, chat.scrollHeight);
    first_msg.scrollIntoView(true);
}


function check_pos() {
    if (chat.scrollTop == 0) {
        load_more_msgs();
        chat.onscroll = null;  // disable until finished loading all new msgs
    }
}


function update(chat_id, ...chat_msgs_list_of_dicts) {
    if (chat_id !== chat.chat_id) return null;
    let from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time, msg_row, keys;
    for (let chat_msgs in chat_msgs_list_of_dicts) {
        keys = Object.keys(chat_msgs);
        keys.sort();
        for (let msg_index in chat_msgs) {
            if (msg_index > last_msg_index) break;
            [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time] = chat_msgs[msg_index];
            //
            // check if deleted and change color
            msg_row = document.getElementById("msg_" + msg_index);
            msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
        }
    }
}


function get_open_chat_id() {
    return chat.chat_id;
}


async function load_chat_buttons() {
    // {chat_id: [name, last_msg, time]}
    let chat_ids = JSON.parse(await eel.get_all_chat_ids()());
    let chat_id, chat_name, last_message, time, chat_type;
    for (chat_id in chat_ids) {
        [chat_name, last_message, time, chat_type] = chat_ids[chat_id];
        if (document.getElementById(chat_id) !== null) continue;  // already exists
        chat_box_left("imgs/profile.jpg", chat_name, last_message, time, chat_id, chat_type);
    }
    setTimeout(load_chat_buttons, 10_000);  // every 10 seconds update
}


async function ask_for_username() {
    username = await eel.get_username()();
}


function chat_search() {
    let search_key = document.getElementById("search_chat").value.toLowerCase();
    if (search_key == current_search_key) return;  // prevet calculation for no reason
    current_search_key = search_key;
    let chat_buttons = document.getElementsByClassName("chat");
    let keys = Object.keys(chat_buttons);
    let chat_button, chat_name, last_msg, last_msg_time;
    for (let key in keys) {
        chat_button = chat_buttons[key];
        chat_name = chat_button.getElementsByClassName("chat-name")[0].innerHTML.toLowerCase();
        last_msg = chat_button.getElementsByClassName("chat-last-message")[0].innerHTML.toLowerCase();
        last_msg_time = chat_button.getElementsByClassName("chat-last-message-time")[0].innerHTML.toLowerCase();
        if ((search_key == "group" && chat_button.chat_type == "group") || 
            (search_key == "1 on 1" && chat_button.chat_type == "1 on 1") ||
            chat_name.includes(search_key) || 
            last_msg.includes(search_key) || 
            last_msg_time.includes(search_key) || search_key == "") 
        {
            chat_button.style.visibility = 'visible';
            chat_button.sep.style.visibility = 'visible';
        } else {
            chat_button.style.visibility = 'hidden';
            chat_button.sep.style.visibility = 'hidden';
        }
    }
}


function demo() {
    console.log("demo");
    // create all chat boxes
    for (let i = 1; i < 200; i ++) chat_box_left('imgs/profile.jpg', "test" + i, "holla", "10:43", i);
    for (let i = 1; i < 800; i++) {
        msg_from_me("omer", "aoiushdfoiahsdfoijasdopifjasopdifjasl;dk1234567890uw3n4yct9o7823y4trc908weymcopgfiuweyr", 
        "18:05", i, "msg", [], false, [], "START");
        msg_from_others("someone", "aoiushdfoiahsdfoijasdopifjasopdifjasl;dk12345678909m3cy9t723htf79weuhrfgiuwer", 
        "18:05", i, "msg", [], false, [], "START");
    }
    msg_from_me("omer", "מה קורה", "18:01", 800, "msg", [], false, [], "START");
    // reset_chat_and_status_bar();
    chat.scrollTo(0, chat.scrollHeight);
    console.log("done");
    // eel.hello("Asdfasdf")();
}


function main() {
    console.log("main");
    // ask for username
    ask_for_username();

    // profile picture
    let user_profile_picture = document.getElementById("user-profile-picture");
    user_profile_picture.style.backgroundImage = 'url("imgs/profile.jpg")';

    // window active & inactive event listeners
    window.addEventListener('focus', window_active);
    window.addEventListener('blur', window_inactive);
    if (document.hasFocus()) window_active();
    else window_inactive();

    // load all chat buttons
    load_chat_buttons();

    // bind functions
    // let drawer = document.getElementById('drawer');
    // drawer.onclick = toggleEmojiDrawer;
    let send_btn = document.getElementById('send_msg');
    // event listeners
    send_btn.addEventListener("click", demo);

    // main finish log
    console.log("main setup finished successfully");
}


// Globals
var username;
var last_msg_index;
var current_search_key;
var chat = document.getElementById("chat");
chat.chat_id = "";

// eel
eel.expose(get_open_chat_id);
eel.expose(update);
eel.expose(load_chat_buttons);
eel.expose(main);

main();
// demo();
