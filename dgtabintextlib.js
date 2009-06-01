function replaceSelectionOrInsertAtCursor(myExistingTextField, myNewString)
{
    if (document.selection) {
        // IE-style browser
        myExistingTextField.focus();
        sel = document.selection.createRange();
        sel.text = myNewString;
    } else if (myExistingTextField.selectionStart || myExistingTextField.selectionStart == '0') {
        // Mozilla/Netscape-style browser
        var startPos = myExistingTextField.selectionStart;
        var endPos = myExistingTextField.selectionEnd;
        restoreTop = myExistingTextField.scrollTop;
       
        myExistingTextField.value = myExistingTextField.value.substring(0, startPos) + myNewString + myExistingTextField.value.substring(endPos, myExistingTextField.value.length);
        myExistingTextField.selectionStart = startPos + myNewString.length;
        myExistingTextField.selectionEnd = startPos + myNewString.length;
        // use the same scroll location as before 
        //  so text doesn't "jump around"
        //  (i.e. don't accept browser relocate to unscrolled top)
        myExistingTextField.scrollTop = restoreTop;
    } else {
        // unknown style browser - try something and just hope it works right
        myExistingTextField.value += myNewString;
    }
}

// We are going to catch the TAB key in a browser-independent way 
//  so that we can handle it ourselves
function interceptTab(textControl, keyEvent) {
    var keynum = 0;
    if (keyEvent.keyCode && keyEvent.keyCode != 0) { keynum = keyEvent.keyCode;
    } else if (keyEvent.charCode && keyEvent.charCode != 0) { keynum = keyEvent.charCode;
    } else if (keyEvent.which && keyEvent.which != 0) { keynum = keyEvent.which;
    }
    // if we failed to get keynum, just return and hope we didn't do any damage
    if (keynum == 0) { return true; }

    if (keynum == 9) {
        // TAB key, handle it specially
        replaceSelectionOrInsertAtCursor(textControl, "\t");
        setTimeout("document.getElementById('"+textControl.id+"').focus();",0);    
        return false;
    } else {
        // non-TAB key, let browser handle it normally
        return keynum;

        // note that if there are any 'alerts' above, some browsers 
        //  (ex: Firefox 1.5.0.1) will double the entered key, 
        //  displaying it once right away and a second time on return
    }
}

// sample call
// <textarea ... id="anything, but must be present and must be unique" onKeydown="return interceptTab(this, event)"></textarea>
// works with <input type="text" ...> too
