                            /* General use functions */
function assert(condition, message) {
    // implementation of assert like in python
    if (!condition) throw "Assertion failed - " + message;
}
function sleep(ms) {
    // implementation of time.sleep
    return new Promise(resolve => setTimeout(resolve, ms));
}
function elementInViewport(el) {
    // checks if you can see the entire element or some/all of it is hidden
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
function get_all_selected_users_emails() {
    // returns all the users that the user selected in order to create a new group/chat
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
function get_last_selected_user() {
    // returns the last selected user
    let children = [].slice.call(users_list.getElementsByClassName("chat"));
    let user;
    for (let index in children) {
        user = children[index];
        if (!user.getElementsByClassName("create_chat_or_group_checkbox")[0].checked) return user;
    }
    return null;
}
function select_user(other_email, user_box_div) {
    // select a user
    let checkbox = document.getElementById(other_email);
    if (users_list.childElementCount > 1) {
        if (!checkbox.checked) {
            users_list.insertBefore(user_box_div.sep, users_list.children[2]);
            users_list.insertBefore(user_box_div, user_box_div.sep);
        } else {
            let before_element = get_last_selected_user();
            if (before_element == null) users_list.appendChild(user_box_div.sep);
            else users_list.insertBefore(user_box_div.sep, before_element);
            users_list.insertBefore(user_box_div, user_box_div.sep);
        }
        // users_list.prepend(search_for_non_familiar_user);
        // users_list.prepend(create_new_chat_or_group);
    }
    checkbox.checked = !checkbox.checked;
}

// sort chats
function sort_chats_by_date(chat_buttons, search_key) {
    // sorts the chats by the date of last msg
    let keys, chat_button;
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
        if (keys.length == 1 && chats_list.firstChild == chat_button) continue;
        chats_list.prepend(chat_button.sep);
        chats_list.prepend(chat_button);
    }
    return;
}

// search (in chats/users)
function chat_search(do_anyway=false, changed_buttons=[]) {
    // search a chat - by date, by last msg, by name, by group/chat
    if (!document.getElementById("left").contains(chats_list)) {
        user_search();
        return
    }
    let search_key = document.getElementById("search_chat").value.toLowerCase();
    if (search_key == current_search_key && !do_anyway) return;  // prevet calculation for no reason
    current_search_key = search_key;
    let chat_buttons = [].slice.call(document.getElementsByClassName("chat"));
    let keys = Object.keys(chat_buttons);
    let chat_button, chat_name, last_msg, last_msg_time;
    if  (search_key == "") {
        sort_chats_by_date(do_anyway ? changed_buttons : chat_buttons, search_key);
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
    sort_chats_by_date(do_anyway ? changed_buttons : chat_buttons, search_key);
}
function user_search() {
    // search a user, by email
    if (document.getElementById("left").contains(chats_list)) {
        chat_search();
        return
    }
    let search_key = document.getElementById("search_chat").value.toLowerCase();
    if (search_key == current_search_key) return;  // prevet calculation for no reason
    current_search_key = search_key;
    let users_buttons = [].slice.call(document.getElementsByClassName("chat"));
    let keys = Object.keys(users_buttons);
    let users_button, chat_name;
    if  (search_key == "") {
        for (let key in keys) {
            users_button = users_buttons[key];
            users_button.style.visibility = 'visible';
            users_button.sep.style.visibility = 'visible';
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
    // calls user_search / chat_search depends on what is currently on screen
    if (document.getElementById("left").contains(chats_list)) chat_search();
    else user_search();
}

// load chats/user buttons & toggle chats and users
function chat_box_left(chat_picture_path, chat_name, last_message, 
    last_message_time, chat_id, chat_type, users) {
    // create new chat box and append to chat list

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
    return chat_box_div;
}
function user_box_left(user_picture_path, other_email) {
    // create new user box and append to user list

    // the div of the entire user box
    let user_box_div = document.createElement("div");
    user_box_div.className = "chat";
    user_box_div.id = `user_box_${other_email}`;
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
    user_box_div.addEventListener("click", function() { select_user(other_email, user_box_div) });
}
async function load_chat_buttons() {
    // calls chat_box_left for every chat
    let changed = false;
    let changed_buttons = [];
    if (document.contains(chats_list)) {
        // {chat_id: [chat_name, last_msg, time, chat_type]}
        let chat_ids = JSON.parse(await eel.get_all_chat_ids()());
        let chat_id, chat_name, last_message, time, chat_type, users, number_of_unread_msgs;
        let picture_path;
        let chat_box;
        for (chat_id in chat_ids) {
            [chat_name, last_message, time, chat_type, users, number_of_unread_msgs] = chat_ids[chat_id];
            if (document.getElementById(chat_id) != null) { // already exists
                chat_box = document.getElementById(chat_id);
                if (chat_box.getElementsByClassName("chat-last-message")[0].innerHTML !== last_message 
                    || chat_box.getElementsByClassName("chat-last-message-time")[0].innerHTML !== time) 
                    {
                    chat_box.getElementsByClassName("chat-last-message")[0].innerHTML = last_message;
                    chat_box.getElementsByClassName("chat-last-message-time")[0].innerHTML = time;
                    changed = true;
                    changed_buttons.push(chat_box);
                }
                let chat_name = chat_box.getElementsByClassName("chat-name")[0];
                if (number_of_unread_msgs !== 0) {
                    chat_name.style.color = "#0b721c";
                    if (chat_name.innerHTML.includes(" - (")) {
                        chat_name.innerHTML = chat_name.innerHTML.split(" - ")[0] + ` - (${number_of_unread_msgs})`;
                    } else chat_name.innerHTML = chat_name.innerHTML + ` - (${number_of_unread_msgs})`;
                } else {
                    chat_name.style.color = "white";
                    if (chat_name.innerHTML.includes(" - (")) chat_name.innerHTML = chat_name.innerHTML.split(" - ")[0];
                }
                continue;
            }
            changed = true;
            if (chat_type === "group") {
                picture_path = `url("${email}/${chat_id}/group_picture.png")`;
            } else {
                let other_user_email;
                if (users[0] != email) other_user_email = users[0];
                else other_user_email = users[1];
                picture_path = `url("${email}/profile_pictures/${other_user_email}_profile_picture.png")`;
            }
            changed_buttons.push(chat_box_left(picture_path, chat_name, last_message, time, chat_id, chat_type, users));
        }
        if (changed) chat_search(true, changed_buttons);
    }
    setTimeout(load_chat_buttons, 100);  // update again in 100 milliseconds
}
async function load_users_buttons() {
    // calls user_box_left for every user
    users_list.innerHTML = "";
    users_list.appendChild(create_new_chat_or_group);
    users_list.appendChild(search_for_non_familiar_user);
    let known_to_user = JSON.parse(await eel.get_known_to_user()());
    let other_email;
    for (let index in known_to_user) {
        other_email = known_to_user[index];
        let picture_path = `url("${email}/profile_pictures/${other_email}_profile_picture.png")`;
        user_box_left(picture_path, other_email);
    }
}
function toggle_chats_users() {
    // toggle between chat list & user list
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
    // change chat visibility, if a chat is open and his button is clicked again, it
    // will become hidden, click again to make it visible
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
    // loads a max of 800 msgs, this is the initial load of the chat
    // if a user scrolls to the top of the chat and there are more messages
    // they will be loaded, I choose to do this like that because it's more efficient
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
        if (parseInt(last_msg_index) < parseInt(msg_index)) last_msg_index = parseInt(msg_index);
    }
}
async function update_last_seen() {
    // updates the last seen status of current chat (only for 1 on 1 chats)
    if (current_chat_other_email != "") {
        status_bar_last_seen.innerHTML = await eel.get_user_last_seen(current_chat_other_email)();
    }
    setTimeout(update_last_seen, 1_000);
}
async function load_chat(chat_name, chat_id, chat_type, users) {
    // changes the elements that need to be change and calls the initial load
    // of messages, changes the picture and the event listeners
    document.getElementById("msg_input").focus();
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
        current_chat_other_email = "";
        status_bar_picture.onclick = function () { upload_group_picture(chat_id) };
        status_bar_picture.style.cursor = "pointer";
    }
    else {
        let other_user_email;
        if (users[0] != email) other_user_email = users[0];
        else other_user_email = users[1];
        status_bar_picture.style.backgroundImage = `url("${email}/profile_pictures/${other_user_email}_profile_picture.png")`;
        status_bar_last_seen.innerHTML = await eel.get_user_last_seen(other_user_email)();
        current_chat_other_email = other_user_email;  // in order to update every 1 second
        status_bar_picture.onclick = null;
        status_bar_picture.style.cursor = "context-menu";
    }
    last_msg_index = 0;
    chat.chat_id = chat_id;
    let chat_msgs = JSON.parse(await eel.get_chat_msgs(chat_id)());
    if (chat_msgs === {}) return;  // chat is empty
    await load_msgs(chat_msgs);
    status_bar_name.innerHTML = chat_name;
    chat.scrollTo(0, chat.scrollHeight);
    setTimeout(function() { chat.scrollTo(0, chat.scrollHeight); }, 200);
    await eel.mark_as_seen(get_open_chat_id())();
}
async function load_more_msgs() {
    // if the user scrolled to the top of the chat this function will be called
    // it will ask the python for older messages in this chat, if there are
    // it will load another 800 messages
    chat.scrollBy(0, 20);
    let chat_msgs = JSON.parse(await eel.get_more_msgs()());
    if (Object.keys(chat_msgs).length === 0) return;  // no more messages
    let first_msg = chat.firstChild;
    let chat_id = chat.chat_id;
    console.log(`loading more messages (id: '${chat_id}')`);
    await load_msgs(chat_msgs, "START");
    chat.onscroll = check_pos;  // re-allow loading more msgs
    chat.scrollTo(0, chat.scrollHeight);
    first_msg.scrollIntoView(true);
    chat.scrollBy(0, -200);  // show some of the new loaded messages
}
function check_pos() {
    // when the chat is scrolled this function is called
    // when it reaches the top it will call load_more_msgs
    if (chat.scrollTop == 0) {
        chat.onscroll = null;  // disable until finished loading all new msgs
        load_more_msgs();
    }
}
// eel.expose
function update(chat_id, chat_msgs) {
    // if there is a new msg after the loading of
    // the chat this function is responsible to
    // adding that message, also if a msg was edited
    // this function will change the msg
    if (chat_id !== chat.chat_id) return null;
    chat_msgs = JSON.parse(chat_msgs);
    let from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time, msg_row;
    let new_messages = {};
    let scrollToBottom = false;
    if (chat.scrollHeight - chat.scrollTop - chat.offsetHeight <= 200) scrollToBottom = true;
    for (let msg_index in chat_msgs) {
        [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time] = chat_msgs[msg_index];
        if (parseInt(msg_index) > parseInt(last_msg_index)) {  // new messages
            new_messages[msg_index] = [from_user, msg, msg_type, deleted_for, deleted_for_all, seen_by, time];
            continue;
        }
        msg_row = document.getElementById(`msg_${msg_index}`);
        // old message that has been changed
        if (deleted_for.includes(email)) {
            if (msg_row !== null) {
                msg_row.remove();
            }
        } else if (deleted_for_all && msg_type === "msg") {
            if (msg_row !== null) {
                msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;  // This message was deleted.
                if (from_user === email) msg_row.getElementsByClassName("my_msg_box")[0].style.backgroundColor = "#232323";
                else msg_row.getElementsByClassName("msg_box")[0].style.backgroundColor = "#232323";
            }
        } else if (msg_row !== null && deleted_for_all && msg_type === "file" && 
                   msg_row.getElementsByClassName("msg_image").length === 1) {
            msg_row.getElementsByClassName("msg_image")[0].remove();
            if (from_user === email) {
                msg_row.getElementsByClassName("my_msg_box")[0].remove();
                let my_msg_box = window.my_msg_row.getElementsByClassName("my_msg_box")[0].cloneNode(true);
                my_msg_box.getElementsByClassName("msg_text")[0].innerHTML = msg;
                msg_row.appendChild(my_msg_box);
                msg_row.getElementsByClassName("my_msg_box")[0].style.backgroundColor = "#232323";
            } else {
                msg_row.getElementsByClassName("msg_box")[0].remove();
                let msg_box = window.msg_row.getElementsByClassName("msg_box")[0].cloneNode(true);
                msg_box.getElementsByClassName("msg_text")[0].innerHTML = msg;
                msg_box.getElementsByClassName("msg_sender")[0].innerHTML = from_user;
                msg_row.appendChild(msg_box);
                msg_row.getElementsByClassName("msg_box")[0].style.backgroundColor = "#232323";
                msg_row.getElementsByClassName("msg_box")[0].style.backgroundColor = "#232323";
            }
        }
    }
    load_msgs(new_messages);
    if (scrollToBottom) setTimeout(function() { chat.scrollTo(0, chat.scrollHeight); }, 200);;
}

function adjust_msgs_input_width() {
    // adjust the input bar width according to the size of the window
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
    // rerturns the current chat id
    return chat.chat_id;
}


                                    /* Messages */

function message_options(msg_index, full_sender, seen_by, deleted_for_all) {
    // messages options - delete for me/all , read receipts
    let popup = document.createElement("dialog");
    let delete_for_me = document.createElement("button");
    delete_for_me.innerHTML = "Delete for me";
    delete_for_me.addEventListener("click", async function() {
        popup.close();
        document.getElementsByTagName("body")[0].removeChild(popup);
        await eel.delete_message_for_me(get_open_chat_id(), msg_index)();
    });
    popup.appendChild(delete_for_me);
    if (full_sender === email && !deleted_for_all) {
        let delete_for_all = document.createElement("button");
        delete_for_all.innerHTML = "Delete for all";
        delete_for_all.addEventListener("click", async function() {
            popup.close();
            document.getElementsByTagName("body")[0].removeChild(popup);
            await eel.delete_message_for_everyone(get_open_chat_id(), msg_index)();
        });
        popup.appendChild(delete_for_all);
    }
    let read_receipts = document.createElement("button");
    read_receipts.innerHTML = "Read receipts";  // TODO: implement read receipts
    popup.appendChild(read_receipts);
    //
    let close = document.createElement("button");
    close.innerHTML = "Close";
    close.addEventListener("click", function() { popup.close(); });
    popup.appendChild(close);
    //
    document.getElementsByTagName("body")[0].prepend(popup);
    popup.showModal();
}
function handle_msg_length(msg) {
    // adds \n if needed to limit msg row length
    let max_chars = 65;
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
    return msg + "\n\n";
}


function append_to_chat(position, element) {
    // append a message to the chat, initial load will use END
    // load more msgs will use START
    if (position === "END") {
        chat.appendChild(element);
        chat.appendChild(window.clear.cloneNode(true));
    } else {
        chat.prepend(window.clear.cloneNode(true));
        chat.prepend(element);
    }
}
/* 
TODO: add time - 
      when this msg time (date) is different from 
      the last one (maybe with 'sticky' position in css)
*/
function add_msg(from, sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
        // create a new message from all types
        // types:
        // This message was deleted.
        // msg from you, msg from others
        // file msg from you, file msg from others
        // add and remove message (add user and remove user from group)
        assert(
            position === "END" || position === "START",
            `msg_from_me: param position must be either 'END' or 'START', got '${position}'`
        );
        assert(
            msg_type == "msg" || msg_type == "file" || msg_type == "remove" || msg_type == "add",
            `msg_from_me: param msg_type must be either 'msg' or 'file' or 'remove' or 'add', got '${msg_type}'`
        );
        let full_sender = sender;
        sender = sender.split("@");
        sender = sender.slice(0, sender.length - 1).join("@") + ":";
        if (deleted_for_all) {
            // This message was deleted.
            let this_msg_row = from == "me" ? window.my_msg_row.cloneNode(true) : window.msg_row.cloneNode(true);
            this_msg_row.id = `msg_${msg_index}`;
            this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
            let msg_box = full_sender === email ? this_msg_row.getElementsByClassName("my_msg_box")[0] : this_msg_row.getElementsByClassName("msg_box")[0];
            msg_box.style.backgroundColor = "#232323";
            // append msg row to chat
            append_to_chat(position, this_msg_row);
            // add event listener
            this_msg_row.addEventListener("contextmenu", function() { message_options(msg_index, full_sender, seen_by, deleted_for_all); }) // right click
        } else if (deleted_for.includes(email)) {
            return;
        } else if (msg_type === "msg") {
            msg = handle_msg_length(msg);
            let this_msg_row = from == "me" ? window.my_msg_row.cloneNode(true) : window.msg_row.cloneNode(true);
            this_msg_row.id = `msg_${msg_index}`;
            this_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
            // msg_picture.style.backgroundImage = `url("${email}/${email}_profile_picture.png")`;
            if (full_sender !== email) {
                this_msg_row.getElementsByClassName("msg_sender")[0].innerHTML = sender;
                let msg_picture = this_msg_row.getElementsByClassName("msg_sender_picture")[0];
                msg_picture.style.backgroundImage = `url("${email}/profile_pictures/${full_sender}_profile_picture.png")`;
            }
            // append msg row to chat
            append_to_chat(position, this_msg_row);
            // add event listener
            this_msg_row.addEventListener("contextmenu", function() { message_options(msg_index, full_sender, seen_by, deleted_for_all); }) // right click
        } else if (msg_type === "file") {
            msg = msg.replaceAll("\\", "/");
            let display_file = false;
            for (let index in image_types) {
                if (msg.toLowerCase().endsWith(image_types[index])) {
                    display_file = true;
                    break;
                }
            }
            let voice_recording = msg.toLowerCase().endsWith(".wav") ? true : false;
            if (display_file) {
                let photo_row = from == "me" ? window.my_photo_msg_row.cloneNode(true) : window.photo_msg_row.cloneNode(true);
                photo_row.getElementsByClassName("msg_image")[0].src = `${email}/${msg}`;
                photo_row.id = `msg_${msg_index}`;
                photo_row.getElementsByClassName("msg_image")[0].onclick = async function () { await eel.start_file(`${email}/${msg}`); };
                append_to_chat(position, photo_row);
                photo_row.addEventListener("contextmenu", function() { message_options(msg_index, full_sender, seen_by, deleted_for_all); }) // right click
            } else if (voice_recording) {
                let file_row = from == "me" ? window.my_photo_msg_row.cloneNode(true) : window.photo_msg_row.cloneNode(true);
                file_row.getElementsByClassName("msg_image")[0].remove();
                file_row.id = `msg_${msg_index}`;
                let recording_options_box = document.createElement("audio");
                recording_options_box.controls = true;
                recording_options_box.id = "audio_player";
                let audio_file = document.createElement("source");
                audio_file.src = `${email}/${msg}`;
                audio_file.id = "audio_file";
                audio_file.type = "audio/wav";
                recording_options_box.appendChild(audio_file);
                if (from == "me") file_row.getElementsByClassName("my_msg_box")[0].appendChild(recording_options_box);
                else file_row.getElementsByClassName("msg_box")[0].appendChild(recording_options_box);

                append_to_chat(position, file_row);
                file_row.addEventListener("contextmenu", function() { message_options(msg_index, full_sender, seen_by, deleted_for_all); }) // right click
            } else {
                let file_row = from == "me" ? window.my_photo_msg_row.cloneNode(true) : window.photo_msg_row.cloneNode(true);
                file_row.getElementsByClassName("msg_image")[0].className = "msg_file";
                file_row.id = `msg_${msg_index}`;
                let file_name = msg.split("/");
                file_name = file_name[file_name.length - 1];
                file_row.getElementsByClassName("msg_file")[0].alt = file_name;
                file_row.getElementsByClassName("msg_file")[0].onclick = async function () { await eel.start_file(`${email}/${msg}`); };
                append_to_chat(position, file_row);
                file_row.addEventListener("contextmenu", function() { message_options(msg_index, full_sender, seen_by, deleted_for_all); }) // right click
            }
        } else if (msg_type === "remove" || msg_type === "add") {
           let add_remove_msg_row = window.add_remove_msg_row.cloneNode(true);
           add_remove_msg_row.getElementsByClassName("msg_text")[0].innerHTML = msg;
           append_to_chat(position, add_remove_msg_row);
        }
}
function msg_from_me(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
        // call add message on a message that you sent
    add_msg("me", sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position);
}
function msg_from_others(sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position="END") {
        // call add_msg on a message that was sent by someone else
    add_msg("others", sender, msg, time, msg_index, msg_type, deleted_for, 
    deleted_for_all, seen_by, position);
}


                            /* Window active & inactive */

function window_active() {
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

function window_inactive() {
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
    // add the emoji that was pressed
    document.getElementById('input_bar').value += emoji;
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
    input_bar.focus();
    let ok = await eel.send_message(msg, get_open_chat_id())();
    if (!ok && input_bar.value === "") input_bar.value = msg;
}

async function familiarize_user_with() {
    // checks if user exists, if it does it will make
    // him "known" to you and add him to users list
    // so you can create a new chat/group with him
    let user_search_input = document.getElementById("non_familiar_user_search_input");
    let other_email = user_search_input.value;
    user_search_input.value = "";
    if (other_email != "" && other_email.includes("@") && 
        other_email.length > 2 && other_email.includes(".") &&
        !other_email.includes(" ")
        ) {
        let exists = await eel.familiarize_user_with(other_email)();
        await sleep(1000);
        if (exists) { toggle_chats_users(); toggle_chats_users(); }
    } else alert("Invalid user, user is an email, needs to have '@' & '.' and can't contain spaces.")
}

// new chat/group
async function new_chat(other_email) {
    await eel.new_chat(other_email)();
}
async function new_group(other_emails, group_name) {
    await eel.new_group(other_emails, group_name)();
}
function new_group_or_chat() {
    // checks if a new group should be created or a new chat
    // if group asks for group name
    // finally toggles between users list to chats list
    let checked_users = get_all_selected_users_emails();
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


async function add_user_to_group() {  // TODO create a button for this and implement function
    // popup with all known users - group users and select the user to add
    // await eel.add_user_to_group(other_email, get_open_chat_id());
}


async function remove_user_from_group() {  // TODO create a button for this and implement function
    // popup with all group users and select the user to remove
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
    // stop recording and let user decide if he wants to send
    // the recorded audio or delete it (he can listen to it)
    let ok = await eel.stop_recording()();
    if (ok) {
        let record_btn = document.getElementById("record_msg");
        record_btn.name = "mic-outline";
        record_btn.onclick = start_recording;
        record_btn.title = "Start recording";
    }
}
function restore_input() {
    // resotre input after displaying recording options
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
    // display the recording options - delete, send & listen to audio
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

async function add_hang_up_btn_and_check_call_status() {
    // add a button on the top that allows to hang up
    // also checks if the call ended, if so removes the button
    // and alerts the user
    let hang_up_call_btn = document.createElement("button");
    hang_up_call_btn.innerHTML = "Hang Up";
    hang_up_call_btn.id = "hang_up_call_btn";
    hang_up_call_btn.addEventListener("click", async function() {
        await eel.hang_up_call()();
        hang_up_call_btn.remove();
    });
    let body = document.getElementsByTagName("body")[0];
    body.prepend(hang_up_call_btn);
    async function check_call_status() {
        // checks if the call is still running
        let is_running = await eel.check_ongoing_call()();
        if (is_running) setTimeout(check_call_status, 2500);
        else {
            let hang_up_call_btn = document.getElementById("hang_up_call_btn");
            if (hang_up_call_btn !== null) {
                hang_up_call_btn.remove();
                alert("Call ended");
            }
        }
    }
    check_call_status();
}

async function make_call() {
    // start a call with the current chat/group
    if (document.getElementById("hang_up_call_btn") !== null) {
        alert("Already in a call, hang up to start a new one.");
        return;
    }
    let chat_id = get_open_chat_id();
    if (chat_id !== "") {
        let status = await eel.make_call(chat_id)();
        if (status) add_hang_up_btn_and_check_call_status();
        else alert("Call failed.");
    }
}

function ongoing_call(group_name, port) {
    // show a popup and let the user decide
    // if he wants to answer the call or ignore
    let popup = document.createElement("dialog");
    let group_name_label = document.createElement("h1");
    group_name_label.innerHTML = group_name;
    let answer = document.createElement("button");
    answer.innerHTML = "Answer Call";
    answer.addEventListener("click", async function() {
        popup.close();
        popup.remove();
        if (document.getElementById("hang_up_call_btn") !== null) {  // there is an ongoing call
            let what_to_do = prompt("Already in a call, do you want to hang up? [y/n] ");
            while (what_to_do != null && 
                   (what_to_do == "" || !what_to_do.replace(/\s/g, '').length) &&
                   what_to_do !== "y" && what_to_do !== "Y" && what_to_do !== "yes" && what_to_do !== "YES" &&
                   what_to_do !== "n" && what_to_do !== "N" && what_to_do !== "no" && what_to_do !== "NO"
            ) {
                what_to_do = prompt("Already in a call, do you want to hang up? [y/n] ");
            }
            if (what_to_do !== "y" && what_to_do !== "Y" && what_to_do !== "yes" && what_to_do !== "YES"){
                return;
            } else eel.hang_up_call()();
        }
        await eel.answer_call(port)();
        add_hang_up_btn_and_check_call_status();
    });
    let ignore = document.createElement("button");
    ignore.innerHTML = "Ignore Call";
    ignore.addEventListener("click", function() { popup.close(); popup.remove(); });
    popup.appendChild(group_name_label);
    popup.appendChild(answer);
    popup.appendChild(ignore);
    document.getElementsByTagName("body")[0].prepend(popup);
    popup.showModal();
}

async function upload_profile_picture() {
    await eel.upload_profile_picture()();
}

async function upload_group_picture(chat_id) {
    await eel.upload_group_picture(chat_id)();
}


                                    /* Main Setup */


// eel.expose
async function main() {
    // main setup - start app
    console.log("main");
    // start the python updater
    await eel.start_app()();
    // ask for email & username
    await ask_for_email();
    await ask_for_username();
    window.title += ` - ${username}`

    // profile picture
    let user_profile_picture = document.getElementById("user-profile-picture");
    user_profile_picture.style.backgroundImage = `url("${email}/${email}_profile_picture.png")`;

    // load all chat buttons
    load_chat_buttons();
    // adjust input width on loadup
    adjust_msgs_input_width();

    // start last seen updater, call it once and it will call it-self
    await update_last_seen();

    // Event listeners
    // window resize, resize input width
    window.addEventListener("resize", adjust_msgs_input_width);
    // window active & inactive event listeners
    window.addEventListener('focus', window_active);
    window.addEventListener('blur', window_inactive);
    // current state
    if (document.hasFocus()) window_active();
    else window_inactive();
    window.addEventListener("beforeunload", function () { eel.close_program()(); })

    // TODO: uncomment the next lines
    
    // block special keys
    // document.onkeydown = function (e) {
    //     if (e.key === "F1" || e.key === "F3" || e.key === "F5" || 
    //         e.key === "F7" || e.key === "F12") {
    //         return false;
    //     }
    // };

    // main finish log
    console.log("main setup finished successfully");
}


                                /* Globals */
var image_types = [".jpeg", ".webp", ".gif", ".png", ".apng", ".svg", ".bmp", ".ico", ".jpg"];
var email;  // email
var username; // username
//
var last_msg_index;  // the index number of the most recent msg in current chat
var current_search_key;  // current search input (of chat buttons)
// the chat
var chat = document.getElementById("chat");  // the chat div
chat.chat_id = "";
// chat status bar
var status_bar_name = document.getElementById("status-bar-name");  // chat name
var status_bar_picture = document.getElementById("status-bar-picture");  // chat picture
var status_bar_last_seen = document.getElementById("status-bar-last-seen");  // chat lst seen
var current_chat_other_email = "";  // if one on one chat, it will contaim the email of the other user
// chat actions & input
var chat_actions = document.getElementById("chat_actions");  // chat actions (file, emoji, send)
var input_bar_box = document.getElementById("input_box");  // input message
// chat list
var chats_list = document.getElementsByClassName("chats_list")[0];  // list of chats/groups
// new chat/group
var users_list = document.createElement("div");  // list of users (for creating chats/groups)
users_list.className = "chats_list";
var create_new_chat_or_group = document.createElement("button");  // create new chat/group btn
create_new_chat_or_group.id = "create_chat_or_group";
create_new_chat_or_group.onclick = new_group_or_chat;
create_new_chat_or_group.innerHTML = "Create";
var search_for_non_familiar_user = document.createElement("div");  // search user (for new chat/group) box
search_for_non_familiar_user.id = "search_for_non_familiar_user";
let non_familiar_user_search_input = document.createElement("input");  // input of username to search
non_familiar_user_search_input.id = "non_familiar_user_search_input";
non_familiar_user_search_input.placeholder = "Search for other users";
search_for_non_familiar_user.appendChild(non_familiar_user_search_input);
let non_familiar_user_search_btn = document.createElement("button");
non_familiar_user_search_btn.id = "non_familiar_user_search_btn";
non_familiar_user_search_btn.innerHTML = "Search";
non_familiar_user_search_btn.onclick = familiarize_user_with;
search_for_non_familiar_user.appendChild(non_familiar_user_search_btn);  // button to trigger search

var message_options_window;
var call_options_window;

// eel
eel.expose(get_open_chat_id);
eel.expose(update);
eel.expose(display_recording_options);
eel.expose(ongoing_call);

main();


/*                                    TODOS
1. need to add buttons for adding & removing users when a chat is 'group'
   and implement the functions to select the users to remove/add
2. messages options - seen list?
*/
