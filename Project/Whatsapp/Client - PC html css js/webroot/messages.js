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
// // msg sender picture
// var my_msg_sender_picture = document.createElement("div");
// my_msg_sender_picture.className = "msg_sender_picture";
// // my_msg_sender_picture.style.backgroundImage = "";
// // msg sender
// var my_msg_sender = document.createElement("div");
// my_msg_sender.className = "msg_sender";
// // my_msg_sender.innerHTML = sender;
// msg text
var my_msg_text = document.createElement("div");
my_msg_text.className = "msg_text";
// my_msg_text.innerHTML = msg;
// msg time
// var my_msg_time = document.createElement("div");
// my_msg_time.className = "msg_time";
// my_msg_time.innerHTML = time;
// append all elements to msg row
// // my_text_and_time.appendChild(my_msg_sender_picture);
// // my_text_and_time.appendChild(my_msg_sender);
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
var msg_sender_picture = document.createElement("div");
msg_sender_picture.className = "msg_sender_picture";
// my_msg_sender_picture.style.backgroundImage = "";
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
text_and_time.appendChild(msg_sender_picture);
text_and_time.appendChild(msg_sender);
text_and_time.appendChild(msg_text);
// text_and_time.appendChild(msg_time);
msg_box.appendChild(text_and_time);
msg_row.appendChild(msg_box);

window.msg_row = msg_row;

/* ------------------------------------------------------------------ */

var clear = document.createElement("div");
clear.className = "clear";
window.clear = clear;

/* ------------------------------------------------------------------ */

var my_photo_msg_row = document.createElement("div");
my_photo_msg_row.className = "my_msg_row";
var my_photo_msg_box = document.createElement("div");
my_photo_msg_box.className = "my_msg_box";
var my_photo = document.createElement("img");
my_photo.className = "msg_image";
my_photo_msg_box.appendChild(my_photo);
my_photo_msg_row.appendChild(my_photo_msg_box);

window.my_photo_msg_row = my_photo_msg_row;

/* ------------------------------------------------------------------ */

var photo_msg_row = document.createElement("div");
photo_msg_row.className = "msg_row";
var photo_msg_box = document.createElement("div");
photo_msg_box.className = "msg_box";
var photo = document.createElement("img");
photo.className = "msg_image";
photo_msg_box.appendChild(photo);
photo_msg_row.appendChild(photo_msg_box);

window.photo_msg_row = photo_msg_row;

/* ------------------------------------------------------------------ */

var add_remove_msg_row = document.createElement("div");
add_remove_msg_row.className = "add_remove_msg_row";
var add_remove_msg_box = document.createElement("div");
add_remove_msg_box.className = "msg_box";
var add_remove_msg_data = document.createElement("div");
add_remove_msg_data.className = "msg_data";
var add_remove_msg_text = document.createElement("div");
add_remove_msg_text.className = "msg_text";
add_remove_msg_data.appendChild(add_remove_msg_text);
add_remove_msg_box.appendChild(add_remove_msg_data);
add_remove_msg_row.appendChild(add_remove_msg_box);

window.add_remove_msg_row = add_remove_msg_row;

/* ------------------------------------------------------------------ */
