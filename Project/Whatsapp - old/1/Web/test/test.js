function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function welcome() {
    document.getElementById("everyone").hidden = false;
    document.getElementById("yuval_shaar").hidden = true;
    document.getElementById("someone_else").hidden = true;
}


const eatRAM_div = document.getElementById("eatRAM");
var fuck_off_div = document.createElement("div");
fuck_off_div.innerHTML = "Fuck Off"
for (var i = 0; i < 0; i++) {
    let random_div = document.createElement("div");
    fuck_off_div.appendChild(random_div);
}


function eatRAM() {
    fuck_off_copy = fuck_off_div.cloneNode(true);
    eatRAM_div.appendChild(fuck_off_copy);
}

async function func(){
    var audio = new Audio('audio.mp3');
    audio.play();
    setTimeout(func, 5000);
}


async function fuck_off() {
    var d = {1: ["asdasd", "hi"], 2: ["ass", "h"]};
    var one, two;
    for (index in d) {
        [one, two] = d[index];
        console.log(index, ": " + index, one, two);
    }
    // document.getElementById("tzutzik").hidden = false;
    document.getElementById("yuval_shaar").hidden = true;
    document.getElementById("someone_else").hidden = true;
    // func();
    for (let i = 0; i < 1000; i++) {
        eatRAM();
        // await sleep(0.000001);
    }
}

function check_pos() {
    console.log(111);
    console.log(document.getElementById("page").scrollTop);
}