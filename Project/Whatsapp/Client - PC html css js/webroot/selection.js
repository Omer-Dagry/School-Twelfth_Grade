var _tripleClickTimer = 0;
var _mouseDown = false;

document.onmousedown = function() {
    _mouseDown = true;
};

document.onmouseup = function() {
    _mouseDown = false;
};

document.ondblclick = function DoubleClick(evt) {
    ClearSelection();
    window.clearTimeout(_tripleClickTimer);

    //handle triple click selecting whole paragraph
    document.onclick = function() {
        ClearSelection();
    };

    _tripleClickTimer = window.setTimeout(RemoveDocumentClick, 100);
};

function RemoveDocumentClick() {
    if (!_mouseDown) {
        document.onclick = null; 
        return true;
    }

    _tripleClickTimer = window.setTimeout(RemoveDocumentClick, 100);
    return false;
}

function ClearSelection() {
    if (window.getSelection)
        window.getSelection().removeAllRanges();
    else if (document.selection)
        document.selection.empty();
}
