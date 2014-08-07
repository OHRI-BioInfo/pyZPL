<html>
<head>
</head>
<body>
<form action="submit.php" method="post">
<?php

$file = "/home/jbrooks/pyZPL/testlabel.xml";

$parser = xml_parser_create();
$tree = simplexml_load_file($file);

$customElements = $tree->xpath("//*[@id]");

foreach($customElements as $element){
    $attributeID = $element->attributes()->id;
    echo '<input type="checkbox" name="'.$attributeID.'_bool">';
    echo $element->attributes()->id."<br />";
}

?>
<br />
<input type="submit"> 
</form>
</body>
</html>
