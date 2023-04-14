/* Create an global msg (from yourself) because it's faster to copy it when creating a new msg */
// msg row
var my_msg_row = document.createElement("div");
my_msg_row.className = "my_msg_row";
// msg box
var my_msg_box = document.createElement("div");
my_msg_box.className = "my_msg_box";
// msg text and time
var my_text_and_time = document.createElement("div");
my_text_and_time.className = "msg_data";
// msg sender
var my_msg_sender = document.createElement("div");
my_msg_sender.className = "msg_sender";
// my_msg_sender.innerHTML = sender;
// msg text
var my_msg_text = document.createElement("div");
my_msg_text.className = "msg_text";
// my_msg_text.innerHTML = msg;
// msg time
// var my_msg_time = document.createElement("div");
// my_msg_time.className = "msg_time";
// my_msg_time.innerHTML = time;
// append all elements to msg row
my_text_and_time.appendChild(my_msg_sender);
my_text_and_time.appendChild(my_msg_text);
// my_text_and_time.appendChild(my_msg_time);
my_msg_box.appendChild(my_text_and_time);
my_msg_row.appendChild(my_msg_box);

window.my_msg_row = my_msg_row;

/* ------------------------------------------------------------------ */

/* Create an global msg (from others) because it's faster to copy it when creating a new msg */
// msg row
var msg_row = document.createElement("div");
msg_row.className = "msg_row";
// msg box
var msg_box = document.createElement("div");
msg_box.className = "msg_box";
// msg text and time
var text_and_time = document.createElement("div");
text_and_time.className = "msg_data";
// msg sender
var msg_sender = document.createElement("div");
msg_sender.className = "msg_sender";
// msg_sender.innerHTML = sender;
// msg text
var msg_text = document.createElement("div");
msg_text.className = "msg_text";
// msg_text.innerHTML = msg;
// msg time
// var msg_time = document.createElement("div");
// msg_time.className = "msg_time";
// msg_time.innerHTML = time;
// append all elements to msg row
text_and_time.appendChild(msg_sender);
text_and_time.appendChild(msg_text);
// text_and_time.appendChild(msg_time);
msg_box.appendChild(text_and_time);
msg_row.appendChild(msg_box);

window.msg_row = msg_row;
