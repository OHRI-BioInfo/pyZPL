<html>
<head>
</head>
<body>
<form action="submit.php" method="post">
<table border=1 cellpadding=5 style="border-collapse:collapse">
<tr><td><b>Field Name</b></td><td><b>Field Type</b></td><td><b>Field Value</b></td><td><b>Visible</b></td></tr>
<?php

$file = "/home/jbrooks/pyZPL/testlabel.xml";

$parser = xml_parser_create();
$tree = simplexml_load_file($file);

$customElements = $tree->xpath("//*[@id]");

foreach($customElements as $element){
    $fixed = "";
    if($element->attributes()->fixed)
        $fixed = "disabled";
    echo '<tr>';
    $attributeID = $element->attributes()->id;
    echo '<td>'.$attributeID."</td><br />";
    echo '<td style="text-align:center;"><span style="font-family:Lucida Console, Monaco, monospace;">'.$element->getName().'</span></td>';
    echo '<td><input type="text" size="60" name="'.$attributeID.'_string" value="'.$element->__toString().'" '.$fixed.'></td>';
    echo '<td><input type="checkbox" name="'.$attributeID.'_bool"</td>';
    echo '</tr>';
}

?>
</table>
<br />
<input type="submit"> 
</form>
</body>
</html>
