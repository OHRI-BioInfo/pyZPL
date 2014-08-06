<?php

$file = "testlabel.xml";

$parser = xml_parser_create();
$data = file_get_contents($file);

function startElementHandler($parser, $name, $attribs){
     if(array_key_exists("ID",$attribs))
        print 'yep';
}

function endElementHandler($parser, $name){
    return;
}

xml_set_element_handler($parser,"startElementHandler","endElementHandler");

print xml_parse($parser,$data,true);

?>
