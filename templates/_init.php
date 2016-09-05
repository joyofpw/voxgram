<?php
namespace Processwire;

include_once './rest/core/rest.php';
include_once './rest/login/errors.php';

use Rest\Header as Header;
use Rest\Response as Response;
use Login\Errors\InvalidCredentials as InvalidCredentials;

$response = new Response();

// Basic Auth
$username = $sanitizer->text(Header::username());
$password = $sanitizer->text(Header::password());

$authenticated = false;

if ((isset($username) || $username != '') ||
		(isset($password) || $password != '')) {

		if ($username == 'voxgrambot' && 
			$password == '$2a$06$GBsycchhrya5G9T0lacmeudhZym1dHZIGmHrIQ5dU5WcV1Vca8kAq') {

			$authenticated = true;

		} else {

			$response->setError(InvalidCredentials::error());
		}
}

if (!$authenticated) {
	$response->render();
	exit;
}

