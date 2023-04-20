                            /* General use functions */
function assert(condition, message) {
    if (!condition) throw "Assertion failed - " + message;
}
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
function isOverflown(element) {
    return element.scrollHeight > element.clientHeight || element.scrollWidth > element.clientWidth;
}
function elementInViewport(el) {
    var top = el.offsetTop;
    var left = el.offsetLeft;
    var width = el.offsetWidth;
    var height = el.offsetHeight;
  
    while(el.offsetParent) {
      el = el.offsetParent;
      top += el.offsetTop;
      left += el.offsetLeft;
    }
  
    return (
      top >= window.pageYOffset &&
      left >= window.pageXOffset &&
      (top + height) <= (window.pageYOffset + window.innerHeight) &&
      (left + width) <= (window.pageXOffset + window.innerWidth)
    );
}


                                /* Chat Buttons */
// new chat/group
function get_all_checked_users_emails() {
    let checked_users = [];
    let children = [].slice.call(users_list.getElementsByClassName("chat"));
    let user;
    for (let index in children) {
        user = children[index];
        if (user.getElementsByClassName("create_chat_or_group_checkbox")[0].checked){
            checked_users.push(user.getElementsByClassName("chat-name")[0].innerHTML)
        }
    }
    return checked_users;
}
function get_last_checked_user() {
    let children = [].slice.call(users_list.getElementsByClassName("chat"));
    let user;
    for (let index in children) {
        user = children[index];
        if (!user.getElementsByClassName("create_chat_or_group_checkbox")[0].checked) return user;
    }
    return null;
}
function check_user(other_email, user_box_div) {
    let checkbox = document.getElementById(other_email);
    if (users_list.childElementCount > 1) {
        if (!checkbox.checked) {
            users_list.prepend(user_box_div.sep);
            users_list.prepend(user_box_div);
        } else {
            let before_element = get_last_checked_user();
            if (before_element == null) users_list.appendChild(user_box_div.sep);
            else users_list.insertBefore(user_box_div.sep, before_element);
            users_list.insertBefore(user_box_div, user_box_div.sep);
        }
        users_list.prepend(create_new_chat_or_group);
    }
    checkbox.checked = !checkbox.checked;
}

// sort chats
function sort_chats_by_date(chat_buttons, search_key) {
    let keys, chat_button
    chat_buttons.sort(function(a, b) {
        return new Date(a.getElementsByClassName("chat-last-message-time")[0].innerHTML) - 
            new Date(b.getElementsByClassName("chat-last-message-time")[0].innerHTML);
    });
    keys = Object.keys(chat_buttons);
    for (let key in keys) {
        chat_button = chat_buttons[key];
        if (search_key == "") {
            chat_button.style.visibility = 'visible';
            chat_button.sep.style.visibility = 'visible';
        } else if (chat_button.style.visibility == "hidden") continue;
        chats_list.prepend(chat_button.sep);
        chats_list.prepend(chat_button);
    }
    return;
}

// search (in chats/users)
function chat_search() {
    let search_key = document.getElementById("search_chat").value.toLowerCase();
    if (search_key == current_search_key) return;  // prevet calculation for no reason
    current_search_key = search_key;
    let chat_buttons = [].slice.call(document.getElementsByClassName("chat"));
    let keys = Object.keys(chat_buttons);
    let chat_button, chat_name, last_msg, last_msg_time;
    if  (search_key == "") {
        sort_chats_by_date(chat_buttons, search_key); 
        return;
    }
    for (let key in keys) {
        chat_button = chat_buttons[key];
        chat_name = chat_button.getElementsByClassName("chat-name")[0].innerHTML.toLowerCase();
        last_msg = chat_button.getElementsByClassName("chat-last-message")[0].innerHTML.toLowerCase();
        last_msg_time = chat_button.getElementsByClassName("chat-last-message-time")[0].innerHTML.toLowerCase();
        if ((search_key === "group" && chat_button.chat_type === "group") || 
            (search_key === "1 on 1" && chat_button.chat_type === "1 on 1") ||
            chat_name.includes(search_key) || 
            last_msg.includes(search_key) || 
            last_msg_time.includes(search_key) || search_key == chat_name) 
        {
            chat_button.style.visibility = 'visible';
            chat_button.sep.style.visibility = 'visible';
        } else {
            chat_button.style.visibility = 'hidden';
            chat_button.sep.style.visibility = 'hidden';
            chats_list.appendChild(chat_button);
            chats_list.appendChild(chat_button.sep);
        }
    }
    sort_chats_by_date(chat_buttons, search_key);
}
function user_search() {
    let search_key = document.getElementById("search_chat").value.toLowerCase();
    if (search_key == current_search_key) return;  // prevet calculation for no reason
    current_search_key = search_key;
    let users_buttons = [].slice.call(document.getElementsByClassName("chat"));
    let keys = Object.keys(users_buttons);
    let users_button, chat_name, last_msg, last_msg_time;
    if  (search_key == "") {
        for (let key in keys) {
            users_button = users_buttons[key];
            chat_button.style.visibility = 'visible';
            chat_button.sep.style.visibility = 'visible';
        }
        return;
    }
    for (let key in keys) {
        users_button = users_buttons[key];
        chat_name = users_button.getElementsByClassName("chat-name")[0].innerHTML.toLowerCase();
        if ((search_key === "group" && users_button.chat_type === "group") || 
            (search_key === "1 on 1" && users_button.chat_type === "1 on 1") ||
            chat_name.includes(search_key) || search_key == chat_name) 
        {
            users_button.style.visibility = 'visible';
            users_button.sep.style.visibility = 'visible';
        } else {
            users_button.style.visibility = 'hidden';
            users_button.sep.style.visibility = 'hidden';
            users_list.appendChild(users_button);
            users_list.appendChild(users_button.sep);
        }
    }
}
function search() {
    if (left_side.contains(chats_list)) chat_search();
    else user_search();
}

// load chats/user buttons & toggle chats and users
function chat_box_left(chat_picture_path, chat_name, last_message, 
    last_message_time, chat_id, chat_type, users) {
    // the div of the entire chat box
    let chat_box_div = document.createElement("div");
    chat_box_div.className = "chat";
    chat_box_div.id = chat_id;
    chat_box_div.chat_type = chat_type;
    // chat picture div
    let chat_picture_div = document.createElement("div");
    chat_picture_div.className = "chat-picture";
    // if (chat_type === "group") image -> by chat_id else image -> by chat
    chat_picture_div.style.backgroundImage = chat_picture_path;
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
    // append all elements to chat box
    chat_box_div.appendChild(chat_picture_div);
    chat_box_div.appendChild(chat_name_div);
    chat_box_div.appendChild(last_message_div);
    chat_box_div.appendChild(last_message_time_div);
    // chat sep
    let chat_sep = document.createElement("hr");
    chat_sep.className = "rounded-chat-sep";
    // append chat box to chats list
    chats_list.appendChild(chat_box_div);
    chats_list.appendChild(chat_sep);
    // save refrence to sep
    chat_box_div.sep = chat_sep;
    // add event listener
    chat_box_div.addEventListener("click", function() { load_chat(chat_name, chat_id, chat_type, users) });
}
function user_box_left(user_picture_path, other_email) {
    // the div of the entire user box
    let user_box_div = document.createElement("div");
    user_box_div.className = "chat";
    // user picture div
    let user_picture_div = document.createElement("div");
    user_picture_div.className = "chat-picture";
    user_picture_div.style.backgroundImage = user_picture_path;
    // user email div
    let user_email_div = document.createElement("div");
    user_email_div.className = "chat-name";
    user_email_div.innerHTML = other_email;
    // checkbox (add to chat/group or not)
    let checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = other_email;
    checkbox.className = "create_chat_or_group_checkbox";
    // append all elements to chat box
    user_box_div.appendChild(user_picture_div);
    user_box_div.appendChild(user_email_div);
    user_box_div.appendChild(checkbox);
    // user sep
    let user_sep = document.createElement("hr");
    user_sep.className = "rounded-chat-sep";
    // append user box to users list
    users_list.appendChild(user_box_div);
    users_list.appendChild(user_sep);
    // save refrence to sep
    user_box_div.sep = user_sep;
    // add event listener
    user_box_div.addEventListener("click", function() { check_user(other_email, user_box_div) });
}
async function load_chat_buttons() {
    let changed = false;
    if (document.contains(chats_list)) {
        // {chat_id: [chat_name, last_msg, time, chat_type]}
        let chat_ids = JSON.parse(await eel.get_all_chat_ids()());
        let chat_id, chat_name, last_message, time, chat_type, users;
        let picture_path;
        for (chat_id in chat_ids) {
            [chat_name, last_message, time, chat_type, users] = chat_ids[chat_id];
            if (document.getElementById(chat_id) != null) continue;  // already exists
            changed = true;
            if (chat_type === "group") {
                picture_path = `url("${email}/${chat_id}/group_picture.png")`;
            } else {
                if (users[0] != email) other_user_email = users[0];
                else other_user_email = users[1];
                picture_path = `url("${email}/profile_pictures/${other_user_email}_profile_picture.png")`;
            }
            chat_box_left(picture_path, chat_name, last_message, time, chat_id, chat_type, users);
        }
    }
    setTimeout(load_chat_buttons, 2_000);  // every 2 seconds update
    if (document.contains(chats_list) && changed) chat_search();
}
async function load_users_buttons() {
    users_list.innerHTML = "";
    users_list.appendChild(create_new_chat_or_group);
    let known_to_user = JSON.parse(await eel.get_known_to_user()());
    let other_email;
    for (let index in known_to_user) {
        other_email = known_to_user[index];
        picture_path = `url("${email}/profile_pictures/${other_email}_profile_picture.png")`;
        user_box_left(picture_path, other_email);
    }
}
function toggle_chats_users() {
    let left_side = document.getElementById("left");
    if (left_side.contains(chats_list)) {
        left_side.removeChild(chats_list);
        left_side.appendChild(users_list);
        load_users_buttons();
    } else {
        left_side.removeChild(users_list);
        left_side.appendChild(chats_list);
    }
}


                                    /* Chat */
// chat visibility & reset chat when switching between chats
function reset_chat_and_status_bar() {
    // reset elements
    chat.innerHTML = "";
    status_bar_picture.style.backgroundImage = "";
    status_bar_name.innerHTML = "";
    status_bar_last_seen.innerHTML = "";
}
function change_chat_visibility(visibility) {
    if (visibility === "hidden") {
        chat.style.visibility = "hidden";
        status_bar_picture.style.visibility = "hidden";
        status_bar_name.style.visibility = "hidden";
        status_bar_last_seen.style.visibility = "hidden";
    } else if (visibility === "visible") {
        chat.style.visibility = "visible";
        status_bar_picture.style.visibility = "visible";
        status_bar_name.style.visibility = "visible";
        status_bar_last_seen.style.visibility = "visible";
    }
}

// load messages (initial load, load when reaching the top of the chat, update - for changed msgs)
async function load_msgs(chat_msgs, position = "END") {
    let from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time;
    let keys = [];
    for (let key in chat_msgs) {
        keys.push(key);
    }
    // sort messages by index
    keys.sort(function(a, b) {
        return parseInt(a) - parseInt(b);
    });
    // if adding more messages from the top, start from the most recent one
    if (position === "START") keys.reverse();
    let msg_index;
    for (let key in keys) {
        msg_index = keys[key];
        [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time] = chat_msgs[msg_index];
        //
        if (deleted_for.includes(email)) continue;
        if (from_user === email) {
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
async function load_chat(chat_name, chat_id, chat_type, users) {
    if (chat_id == chat.chat_id) {
        change_chat_visibility(chat.style.visibility == "visible" ? "hidden" : "visible");
        return;
    }
    reset_chat_and_status_bar();  // clear chat
    change_chat_visibility("visible");
    console.log(`loading chat (name: '${chat_name}', id: '${chat_id}')`);
    if (chat_type === "group") {
        status_bar_picture.style.backgroundImage = `url("${email}/${chat_id}/group_picture.png")`;
        status_bar_last_seen.innerHTML = "";
    }
    else {
        if (users[0] != email) other_user_email = users[0];
        else other_user_email = users[1];
        status_bar_picture.style.backgroundImage = `url("${email}/profile_pictures/${other_user_email}_profile_picture.png")`;;
        status_bar_last_seen.innerHTML = await eel.get_user_last_seen(other_user_email)();
    }
    last_msg_index = 0;
    chat.chat_id = chat_id;
    let chat_msgs = JSON.parse(await eel.get_chat_msgs(chat_id)());
    if (chat_msgs === {}) return;  // chat is empty
    await load_msgs(chat_msgs);
    status_bar_name.innerHTML = chat_name;
    chat.scrollTo(0, chat.scrollHeight);
}
async function load_more_msgs() {
    let first_msg = chat.firstChild;
    let chat_id = chat.chat_id;
    console.log(`loading more messages (id: '${chat_id}')`);
    let chat_msgs = JSON.parse(await eel.get_more_msgs()());
    if (chat_msgs === {}) return;  // no more messages
    chat.scrollBy(0, 10);
    await load_msgs(chat_msgs, "START");
    chat.onscroll = check_pos;  // re-allow loading more msgs
    chat.scrollTo(0, chat.scrollHeight);
    first_msg.scrollIntoView(true);
    chat.scrollBy(0, -200);  // show some of the new loaded messages
}
function check_pos() {
    if (chat.scrollTop == 0) {
        load_more_msgs();
        chat.onscroll = null;  // disable until finished loading all new msgs
    }
}
// eel.expose
function update(chat_id, ...chat_msgs_list_of_dicts) {
    if (chat_id !== chat.chat_id) return null;
    let from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time, msg_row, keys;
    let new_messages = {};
    for (let chat_msgs in chat_msgs_list_of_dicts) {
        keys = Object.keys(chat_msgs);
        keys.sort(function(a, b) {
            return parseInt(a) - parseInt(b);
        });
        for (let msg_index in chat_msgs) {
            [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time] = chat_msgs[msg_index];
            if (msg_index > last_msg_index) {  // new messages
                new_messages[msg_index] = [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time]
            }
            // old message that has been changed
            // TODO: check if deleted and change color
            msg_row = document.getElementById(`msg_${msg_index}`);
            msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
        }
    }
    load_msgs(new_messages);
}

function adjust_msgs_input_width() {
    let send_btn = document.getElementById("send_msg");
    let msgs_input = document.getElementById("msg_input");
    let upload_file = document.getElementById("upload_file");
    let width = 45;
    while (elementInViewport(send_btn) && elementInViewport(upload_file) && width < 78) {
        width++;
        msgs_input.style.width = `${width}%`;
    }
    while (!elementInViewport(send_btn) && elementInViewport(upload_file) && width > 45) {
        width--;
        msgs_input.style.width = `${width}%`;
    }
    msgs_input.style.width = `${width - 1}%`;
}

// eel.expose
function get_open_chat_id() {
    return chat.chat_id;
}


                                    /* Messages */
// TODO: implement func
function message_options() {

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


/* 
TODO: add time - 
      when this msg time (date) is different from 
      the last one (maybe with 'sticky' position in css)
*/
function add_msg(from, sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
        assert(
            position === "END" || position === "START",
            `msg_from_me: param position must be either 'END' or 'START', got '${position}'`
        );
        assert(
            msg_type == "msg" || msg_type == "file" || msg_type == "remove" || msg_type == "add",
            `msg_from_me: param msg_type must be either 'msg' or 'file' or 'remove' or 'add', got '${msg_type}'`
        );
        sender = sender.split("@");
        sender = sender.slice(0, sender.length - 1).join("@") + ":";
        if (deleted_for_all) {
            // This message was deleted.
        } else if (deleted_for.includes(email)) {
            return;
        } else if (msg_type == "msg") {
            msg = handle_msg_length(msg);
            let this_msg_row = from == "me" ? window.my_msg_row.cloneNode(true) : window.msg_row.cloneNode(true);
            this_msg_row.id = `msg_${msg_index}`;
            this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
            // this_msg_row.getElementsByClassName("msg_time")[0].innerHTML = time;
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
function msg_from_me(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
    add_msg("me", sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END");
}
function msg_from_others(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
    add_msg("others", sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END");
}


                            /* Window active & inactive */

function window_active(evt) {
                    /* Change Color Of Search Sep */
    // remove search bar sep
    let search_bar_box = document.getElementById("search_bar_box");
    let sep = document.getElementById("search_bar_chat_list_sep");
    search_bar_box.removeChild(sep);
    // create new one with green color
    sep = document.createElement("hr");
    sep.style.borderTop = "1px solid rgb(33, 170, 33)";
    sep.style.borderRadius = "5px";
    sep.style.backgroundColor = "rgb(33, 170, 33)";
    sep.style.borderColor = "rgb(33, 170, 33)";
    sep.id = "search_bar_chat_list_sep";
    // append it
    search_bar_box.appendChild(sep);
}

function window_inactive(evt) {
                    /* Change Color Of Search Sep */
    // remove search bar sep
    let search_bar_box = document.getElementById("search_bar_box");
    let sep = document.getElementById("search_bar_chat_list_sep");
    search_bar_box.removeChild(sep);
    // create new one with black color
    sep = document.createElement("hr");
    sep.style.borderTop = "1px solid black";
    sep.style.borderRadius = "5px";
    sep.style.backgroundColor = "black";
    sep.style.borderColor = "black";
    sep.id = "search_bar_chat_list_sep";
    // append it
    search_bar_box.appendChild(sep);
}

                                    /* Emoji */
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

                                /* Necessary Data */
async function ask_for_email() {
    email = await eel.get_email()();
}


async function ask_for_username() {
    username = await eel.get_username()();
}


                                /* Communication */
// send message/file
async function send_file(chat_id, file_path="") {
    await eel.send_file(chat_id, file_path)();
}
async function send_message() {
    let input_bar = document.getElementById("msg_input");
    let msg = input_bar.value;
    input_bar.value = "";  // clear input bar
    await eel.send_message(msg, get_open_chat_id())();
}
// new chat/group
async function new_chat(other_email) {
    console.log(`new chat ${other_email}`)
    await eel.new_chat(other_email)();
}
async function new_group(other_emails, group_name) {
    console.log(`new group ${other_emails}`)
    await eel.new_group(other_emails, group_name)();
}
function new_group_or_chat() {
    let checked_users = get_all_checked_users_emails();
    if (checked_users.length == 0) ;
    else if (checked_users.length == 1) new_chat(checked_users[0]);
    else {
        // get group name, can't start with spaces, can't be "" and can't contain only spaces
        let group_name = "";
        while (group_name != null && (group_name == "" || 
               !group_name.replace(/\s/g, '').length || group_name[0] == " ")) {
            group_name = prompt('Please Enter Group Name: ');
        }
        if (group_name != null) new_group(checked_users, group_name);
    }
    toggle_chats_users();
}


async function add_user_to_group() {
    // await eel.add_user_to_group(other_email, get_open_chat_id());
}


async function remove_user_from_group() {
    // await eel.remove_user_from_group(other_email, get_open_chat_id());
}


// recordings functions
async function start_recording() {
    let ok = await eel.start_recording(get_open_chat_id())();
    if (ok) {
        let record_btn = document.getElementById("record_msg");
        record_btn.name = "stop-outline";
        record_btn.onclick = stop_recording;
        record_btn.title = "Stop recording";
    }
}
async function stop_recording() {
    let ok = await eel.stop_recording()();
    if (ok) {
        let record_btn = document.getElementById("record_msg");
        record_btn.name = "mic-outline";
        record_btn.onclick = start_recording;
        record_btn.title = "Start recording";
    }
}
function restore_input() {
    let audio = chat_actions.getElementsByTagName("audio")[0];
    audio.getElementsByTagName("source")[0].remove();
    audio.remove();
    document.getElementById("delete_recording").remove();
    chat_actions.insertBefore(input_bar_box, document.getElementById("right_side_actions"));
    document.getElementById("send_msg").onclick = send_message;
}
async function delete_recording(rec_file_path) {
    restore_input();
    await eel.delete_recording(rec_file_path)();
}
function send_recording(rec_file_path, chat_id) {
    restore_input();
    send_file(chat_id, rec_file_path);
}
// eel.expose
function display_recording_options(rec_file_path, chat_id) {
    if (chat_actions.contains(input_bar_box)) {
        chat_actions.removeChild(input_bar_box);
    } else {
        let delete_btn = document.getElementById("delete_recording");
        delete_btn.click();
        chat_actions.removeChild(input_bar_box);
    }
    let recording_options_box = document.createElement("audio");
    recording_options_box.controls = true;
    recording_options_box.id = "audio_player";
    let audio_file = document.createElement("source");
    audio_file.src = rec_file_path;
    audio_file.id = "audio_file";
    audio_file.type = "audio/wav";
    recording_options_box.appendChild(audio_file);
    chat_actions.insertBefore(recording_options_box, document.getElementById("right_side_actions"));
    let delete_btn = document.createElement("ion-icon");
    delete_btn.name = "trash-outline";
    delete_btn.id = "delete_recording";
    delete_btn.onclick = (rec_file_path) => {delete_recording(rec_file_path)};
    chat_actions.insertBefore(delete_btn, recording_options_box);
    document.getElementById("send_msg").onclick = function() {send_recording(rec_file_path, chat_id)};
}
// end of recordings functions


async function make_call() {
    await eel.make_call(get_open_chat_id());
}


async function upload_profile_picture() {
    await eel.upload_profile_picture()();
}


async function delete_message_for_me() {
    // await eel.delete_message_for_me(chat_id, message_index);
}


async function delete_message_for_everyone() {
    // await eel.delete_message_for_everyone(chat_id, message_index);
}


// eel.expose
async function main() {
    console.log("main");
    // ask for email
    await ask_for_email();
    await ask_for_username();

    // profile picture
    let user_profile_picture = document.getElementById("user-profile-picture");
    user_profile_picture.style.backgroundImage = `url("${email}/${email}_profile_picture.png")`;

    // window active & inactive event listeners
    window.addEventListener('focus', window_active);
    window.addEventListener('blur', window_inactive);
    if (document.hasFocus()) window_active();
    else window_inactive();

    // load all chat buttons
    load_chat_buttons();
    adjust_msgs_input_width();

    // bind functions
    // let drawer = document.getElementById('drawer');
    // drawer.onclick = toggleEmojiDrawer;

    // Event listeners
    window.addEventListener("resize", adjust_msgs_input_width);

    // main finish log
    console.log("main setup finished successfully");
}


                                /* Globals */
var email;  // email
var username; // username
var last_msg_index;  // the index number of the most recent msg in current chat
var current_search_key;  // current search input (of chat buttons)
var chat = document.getElementById("chat");  // the chat div
chat.chat_id = "";
var status_bar_name = document.getElementById("status-bar-name");  // chat name
var status_bar_picture = document.getElementById("status-bar-picture");  // chat picture
var status_bar_last_seen = document.getElementById("status-bar-last-seen");  // chat lst seen
var chat_actions = document.getElementById("chat_actions");  // chat actions (file, emoji, send)
var input_bar_box = document.getElementById("input_box");
var users_list = document.createElement("div");
users_list.className = "chats_list";
var chats_list = document.getElementsByClassName("chats_list")[0];
var create_new_chat_or_group = document.createElement("button");
create_new_chat_or_group.id = "create_chat_or_group";
create_new_chat_or_group.onclick = new_group_or_chat;
create_new_chat_or_group.innerHTML = "Create";

var message_options_window;
var call_options_window;

// eel
eel.expose(get_open_chat_id);
eel.expose(update);
eel.expose(display_recording_options);
eel.expose(main);

main();


/*                                    TODOS
* need to bind function in js to html
* need to add buttons for adding & removing users when a chat is 'group'
* need to add messages options
*/
