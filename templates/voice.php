<?php namespace ProcessWire;

include_once './rest/voices/voice.php';
include_once './rest/voices/errors.php';

use \Rest\Method as Method;
use \Rest\Request as Request;
use \Rest\StatusCode as StatusCode;

use \Voices\Voice as Voice;
use \Voices\Errors\VoiceCouldNotBeDeleted as VoiceCouldNotBeDeleted;
use \Voices\Errors\VoiceCouldNotBeDeletedUserMisMatch as VoiceCouldNotBeDeletedUserMisMatch;

$response->renderErrorAndExitUnlessTheseMethodsAreUsed([Method::DELETE, Method::GET]);

if (Request::isGet()) {
	$voice = new Voice($page);
	$response->data = $voice->output;
	$response->renderAndExit();
}

if (Request::isDelete()) {

	$username = trim($sanitizer->text(Request::getParam('username'))); 

	if ($username == $page->username) {

		try {
			
			$page->setOutputFormatting(false);

			$parent = $page->parent;

			$parent->setOutputFormatting(false);

			$emojis = $parent->usedEmojis;

			$emojis = \Helpers\UTF8::replace(trim($page->about), '', $emojis);

			$parent->usedEmojis = $emojis;

			$parent->save();

			$parent->setOutputFormatting(true);

			$id = $page->id;

			$response->code = StatusCode::accepted();
			
			$response->data['max'] = (int) MAX_VOICES;
			$response->data['quantity'] = (double) $parent->numChildren;
			$response->data['available'] = (int) MAX_VOICES - $parent->numChildren;

			$response->data['_href'] = ['parent' => $parent->httpUrl];

			$response->meta['message'] = __('Item marked for Deletion.');

			$response->render();

			$pages->delete($page, true);

			$logger("Item {$id} deleted by user {$username}");

			$stats = $pages->get('/stats');
			$stats->of(false);
			$stats->totalVoiceFiles -= 1;
			$stats->save();

		} catch (\Exception $e) {
			$logger($e);
			$response->renderErrorAndExit(VoiceCouldNotBeDeleted::error());
		}

	} else {
		$logger("User {$username} is not equal to {$page->username}");
		$response->meta['params'] = ['username' => $username];
		$response->renderErrorAndExit(VoiceCouldNotBeDeletedUserMisMatch::error());
	}
}