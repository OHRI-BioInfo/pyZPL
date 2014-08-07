<?php

$elements = array();

class Element{
}

foreach($_POST as $key => $value){
    $exploded = explode('_',$key);
    $type = $exploded[sizeof($exploded)-1];
    $exploded = explode('_',$key,-1);
    $id = implode('_',$exploded);

    $element = new Element();
    $element->data = $_POST[$id.'_string'];
    if(isset($_POST[$id.'_bool']))
        $element->visible = True;
    else
        $element->visible = False;
    $elements[$id] = $element;
}

$encoded = json_encode($elements);
$command = "python /home/jbrooks/pyZPL/printLabel.py ".escapeshellarg($encoded);
#$command = escapeshellcmd($command);
$output = array();
exec($command,$output);

echo $output[sizeof($output)-1];
?>
