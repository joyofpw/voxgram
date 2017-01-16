<?php namespace Login\Errors;
/**
* A Class that contains errors relating to the login process
*/
include_once __DIR__ . '/../core/rest.php';

use Rest\Errors\Unauthorized as Unauthorized;
use function \ProcessWire\__ as __;

class InvalidCredentials extends Unauthorized {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The credentials you gave were not valid');
		$error->info = __('User or password were incorrect or wrong format of params.');
		$error->uuid = 'kLoginInvalidCredentials';
		$error->number = 1000;
		return $error;
	}
}