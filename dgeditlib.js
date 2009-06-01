function dumpnode(node)
{
    // this function is _not_ used in production,
    //  but it may be very useful for debugging
    alert('dumping node ' + node);
    var lastone = node.childNodes.length;
    var prop;
    for (var i=0; i<lastone; ++i) {
        alert('child ' + i + ' is ' + node.childNodes[i]);
        prop = node.childNodes[i].type;
        alert('type property is ' + prop);
    }
}

function endisableall(parentnode, newvalue)
{
    // called internally by highlightactive,
    //  not currently called directly
    var numberofchildren = parentnode.childNodes.length;
    for (var i=0; i<numberofchildren; ++i) {
        if (parentnode.childNodes[i].type != 'hidden') {
            parentnode.childNodes[i].disabled = newvalue;
        }
    }
}

// this scheme depends on REusing the "title='...'" attribute 
//  of the <td tag for our own purpose (rather than the standardized one)
//  for us title=1 means selecting this box is allowed/meaningful,
//         title=0 means selecting this box is _not_ allowed/meaningful
function highlightactive(rownode, setvalue)
{
    // make the blue outline boxes move
    var localarea = rownode.childNodes[1];
    var mainarea = rownode.childNodes[3];
    var defaultarea = rownode.childNodes[4];

    if (setvalue) {
        localarea.style.border = '5px ridge #26f';
        endisableall(localarea, false);
        mainarea.style.border = '5px ridge transparent';
        defaultarea.style.border = '5px ridge transparent';
    } else {
        localarea.style.border = '5px ridge transparent';
        endisableall(localarea, true);
        if (mainarea.title != 0) {
            mainarea.style.border = '5px ridge #26f';
        } else if (defaultarea.title != 0) {
            defaultarea.style.border = '5px ridge #26f';
        }
    }
}
