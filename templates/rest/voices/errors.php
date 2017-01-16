<?php namespace Voices\Errors;
/**
* A Class that contains errors relating to the login process
*/
include_once __DIR__ . '/../core/rest.php';

use \Rest\Errors\NotFound as NotFound;
use \Rest\Errors\Conflict as Conflict;
use \Rest\Errors\InternalServerError as InternalServerError;
use \Rest\Errors\BadRequest as BadRequest;

use function \ProcessWire\__ as __;

class VoiceParamsNotFound extends BadRequest {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The Params Given al Malformated or Not Present in Request');
		$error->info = __('Some params are needed and must be present in this request.');
		$error->uuid = 'kVoiceParamsNotFound';
		$error->number = 2000;
		return $error;
	}
}

class VoiceCouldNotBeCreated extends InternalServerError {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The voice object could not be created because internal server errors.');
		$error->info = __('There was a conflict when creating a new voice object.');
		$error->uuid = 'kVoiceCouldNotBeCreated';
		$error->number = 2001;
		return $error;
	}
}

class VoiceCouldNotBeCreatedEmojiRepeated extends Conflict {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The voice object could not be created because emojis are already in use.');
		$error->info = __('There was a conflict when creating a new voice object.');
		$error->uuid = 'kVoiceCouldNotBeCreatedEmojiRepeated';
		$error->number = 2002;
		return $error;
	}
}

class VoiceCouldNotBeCreatedLimitExceeded extends Conflict {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The voice object could not be created because the limit was exceeded.');
		$error->info = __('There was a conflict when creating a new voice object.');
		$error->uuid = 'kVoiceCouldNotBeCreatedLimitExceeded';
		$error->number = 2003;
		return $error;
	}
}

class VoiceCouldNotBeCreatedFileIdAlreadyExists extends Conflict {
	public static function error() {
		
		$error = parent::error();
		$error->message = __('The voice object could not be created because the file id already exists.');
		$error->info = __('There was a conflict when creating a new voice object.');
		$error->uuid = 'kVoiceCouldNotBeCreatedFileIdAlreadyExists';
		$error->number = 2004;
		return $error;
	}
}

class VoiceCouldNotBeDeleted extends InternalServerError {
	public static function error() {

		$error = parent::error();

		$error->message = __('The voice object could not be deleted because server problems.');
		
		$error->info = __('There was a conflict when deleting a new voice object.');
		
		$error->uuid = 'kVoiceCouldNotBeDeleted';
		
		$error->number = 2005;
		
		return $error;
	}
}

class VoiceCouldNotBeDeletedUserMisMatch extends BadRequest {
	public static function error() {

		$error = parent::error();

		$error->message = __('The voice object could not be deleted because the user does not belong to this voice.');
		
		$error->info = __('There was a conflict when deleting a new voice object, the user is not the same.');
		
		$error->uuid = 'kVoiceCouldNotBeDeletedUserMisMatch';
		
		$error->number = 2006;
		
		return $error;
	}
}