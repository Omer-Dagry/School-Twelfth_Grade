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
    if (msg.length < 50) return msg;
    var row_length = 0;
    var i = 0;
    while (i < msg.length) {
        if (msg[i] == " " && row_length > 30) {
            msg[i] = "\n";
            row_length = 0;
        }
        else if (row_length == 50) {
            msg = msg.slice(0, i) + "\n" + msg.slice(i);
            row_length = 0;
            i++;
        }
        row_length += 1;
        i++;
    }
    return msg;
}

function msg_from_me(msg, time) {
    msg = handle_msg_length(msg);
    // msg row
    var msg_row = document.createElement("div");
    msg_row.className = "my_msg_row";
    // msg box
    var msg_box = document.createElement("div");
    msg_box.className = "my_msg_box";
    // msg text and time
    var text_and_time = document.createElement("div");
    text_and_time.className = "msg_text_and_time";
    // msg text
    var msg_text = document.createElement("div");
    msg_text.className = "msg_text";
    msg_text.innerHTML = msg;
    // msg time
    var msg_time = document.createElement("div");
    msg_time.className = "msg_time";
    msg_time.innerHTML = time;
    // append all elements to msg row
    text_and_time.appendChild(msg_text);
    text_and_time.appendChild(msg_time);
    msg_box.appendChild(text_and_time);
    msg_row.appendChild(msg_box);
    // append msg row to chat
    var chat = document.getElementById("chat");
    chat.appendChild(msg_row);
    chat.scrollTo(0, chat.scrollHeight);
    // add event listener
    // msg_row.addEventListener("click", function() {func_name(params)})
}


function msg_from_others(msg, time) {
    msg = handle_msg_length(msg);
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
    msg_text.innerHTML = msg;
    // msg time
    var msg_time = document.createElement("div");
    msg_time.className = "msg_time";
    msg_time.innerHTML = time;
    // append all elements to msg row
    text_and_time.appendChild(msg_text);
    text_and_time.appendChild(msg_time);
    msg_box.appendChild(text_and_time);
    msg_row.appendChild(msg_box);
    // append msg row to chat
    var chat = document.getElementById("chat");
    chat.appendChild(msg_row);
    chat.scrollTo(0, chat.scrollHeight);
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
    //
                            /*  */
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
    //
                            /*  */
}


function main() {

    // set profile picture
    var user_profile_picture = document.getElementById("user-profile-picture");
    user_profile_picture.style.backgroundImage = 'url(' + 'images/profile3.jpg' + ")";
    // create all chat boxes
    for (i = 1; i < 200; i++) {
        chat_box_left('images/profile' + i + '.jpg', "test" + i, "holla", "10:43");
        msg_from_me("aoiushdfoiahsdfoijasdopifjasopdifjasl;dk1234567890uw3n4yct9o7823y4trc908weymcopgfiuweyr", "18:05");
        msg_from_others("aoiushdfoiahsdfoijasdopifjasopdifjasl;dk12345678909m3cy9t723htf79weuhrfgiuwer", "18:05");
    }
    console.log("ok");
    // window active
    window.addEventListener('focus', window_active);
    // window inactive
    window.addEventListener('blur', window_inactive);
    if (document.hasFocus()) window_active();
    else window_inactive();
}

main();
