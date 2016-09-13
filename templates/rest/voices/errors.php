<?php
namespace Voices\Errors;
/**
* A Class that contains errors relating to the login process
*/
include_once __DIR__ . '/../core/rest.php';

use Rest\Errors\NotFound as NotFound;
use Rest\Errors\Conflict as Conflict;

use function \Processwire\__ as __;

class VoiceParamsNotFound extends NotFound {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The Params Given al Malformated or Not Present in Request');
		$error->info = __('Some params are needed and must be present in this request.');
		$error->uuid = 'kVoiceParamsNotFound';
		$error->number = 2000;
		return $error;
	}
}

class VoiceCouldNotBeCreated extends Conflict {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The voice object could not be created.');
		$error->info = __('There was a conflict when creating a new voice object.');
		$error->uuid = 'kVoiceCouldNotBeCreated';
		$error->number = 2001;
		return $error;
	}
}