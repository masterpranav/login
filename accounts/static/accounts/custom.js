$(document).ready(function(){

$("#add").click(function(e){
event.preventDefault()
$("#items").append('<div><input type="button" value="add field" id="add"><input type="submit" value="Submit"></div>');	
});

$('#delete').click(function(e){
	$(this).parent('div').remove();
});
});